import pygame
import random
import heapq
import sys

# Initialize Pygame
pygame.init()

# Grid and Screen Dimensions
WIDTH = 800
HEIGHT = WIDTH
GRID_SIZE = 30
CELL_SIZE = WIDTH // GRID_SIZE

# Colors
COLOR_BG = (20, 20, 30)
COLOR_WALL = (50, 50, 70)
COLOR_PATH = (0, 180, 216)      # Light blue for A* path
COLOR_PLAYER = (46, 196, 182)    # Turquoise

# Setup Display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sunjay's Dungeon")
clock = pygame.time.Clock()

# --- MAZE GENERATION (Randomized DFS + Extra Openings for Loops) ---
def generate_maze(size, loop_density):
    maze = [[Cell(x, y) for x in range(size)] for y in range(size)]
    stack = [(1, 1)]
    maze[1][1].terrain_type = "path"

    while stack:
        cx, cy = stack[-1]
        neighbors = []
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            nx, ny = cx + dx, cy + dy
            if 0 < nx < size - 1 and 0 < ny < size - 1 and maze[ny][nx].terrain_type == "wall":
                neighbors.append((nx, ny))
        
        if neighbors:
            nx, ny = random.choice(neighbors)
            maze[cy + (ny - cy) // 2][cx + (nx - cx) // 2].terrain_type = "path"
            maze[ny][nx].terrain_type = "path"
            stack.append((nx, ny))
        else:
            stack.pop()

    for r in range(1, size - 1):
        for c in range(1, size - 1):
            if maze[r][c].terrain_type == "wall":
                if random.random() < loop_density:
                    h_open = (maze[r][c-1].terrain_type == "path" and maze[r][c+1].terrain_type == "path")
                    v_open = (maze[r-1][c].terrain_type == "path" and maze[r+1][c].terrain_type == "path")
                    if h_open or v_open:
                        maze[r][c].terrain_type = "path"
    return maze

class Cell:
    def __init__(self, x, y, terrain_type="wall"):
        self.x = x
        self.y = y
        self.terrain_type = terrain_type

class Player:
    def __init__(self, start_pos, move_cooldown, color):
        self.pos = list(start_pos)
        self.move_cooldown = move_cooldown
        self.color = color

class Ghost:
    def __init__(self, start_pos, move_cooldown, color):
        self.pos = list(start_pos)
        self.move_cooldown = move_cooldown  
        self.color = color
        self.last_move_time = pygame.time.get_ticks()
        self.path = []
        self.state = "patrol"
        self.tracker = [[1 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    def update_state(self, player_pos):
        if self.state == "patrol":
            if self.heuristic(player_pos, tuple(self.pos)) < 7:
                self.state = "chase"
        elif self.state == "chase":
            if self.heuristic(player_pos, tuple(self.pos)) >= 10:
                self.state = "patrol"
                self.path = []

        if self.state == "chase":
            self.move(pygame.time.get_ticks(), maze, player_pos)
        else:
            if pygame.time.get_ticks() - self.last_move_time > self.move_cooldown:
                neighbours = [(self.pos[0] + dx, self.pos[1] + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)] if 0 <= self.pos[0] + dx < GRID_SIZE and 0 <= self.pos[1] + dy < GRID_SIZE and maze[self.pos[1] + dy][self.pos[0] + dx].terrain_type == "path"]
                self.pos = list(random.choices(neighbours, weights=[1 / self.tracker[y][x]**10 for x, y in neighbours])[0]) if neighbours else list(self.pos)
                self.tracker[self.pos[1]][self.pos[0]] += 1
                self.last_move_time = pygame.time.get_ticks()

    def update_path(self, maze, player_pos):
        self.path = self.get_astar_path(maze, tuple(self.pos), tuple(player_pos))

    def move(self, current_time, maze, player_pos):
        if current_time - self.last_move_time > self.move_cooldown:
            self.update_path(maze, player_pos)
            if len(self.path) > 1:
                if tuple(self.pos) in self.path:
                    idx = self.path.index(tuple(self.pos))
                    if idx + 1 < len(self.path):
                        self.pos = list(self.path[idx + 1])
                else:
                    self.pos = list(self.path[0])

            self.update_path(maze, player_pos)
            self.last_move_time = current_time

    def draw_path(self, screen):
        for step in self.path:
            if list(step) != self.pos:
                center_x = step[0] * CELL_SIZE + CELL_SIZE // 2
                center_y = step[1] * CELL_SIZE + CELL_SIZE // 2
                pygame.draw.circle(screen, self.color, (center_x, center_y), CELL_SIZE // 12)

    def draw_label(self, screen):
        font = pygame.font.SysFont(None, CELL_SIZE // 2)
        label = font.render(self.state, True, (255, 255, 255))
        screen.blit(label, (self.pos[0] * CELL_SIZE + 2, self.pos[1] * CELL_SIZE - 10))

    def draw(self, screen):        
        g_rect = pygame.Rect(self.pos[0] * CELL_SIZE + 4, self.pos[1] * CELL_SIZE + 4, CELL_SIZE - 8, CELL_SIZE - 8)
        pygame.draw.rect(screen, self.color, g_rect, border_radius=4)

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_astar_path(self, maze, start, target):
        if start == target:
            return [start]
        
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}
        
        while frontier:
            _, current = heapq.heappop(frontier)
            if current == target:
                break
                
            cx, cy = current
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                next_node = (cx + dx, cy + dy)
                nx, ny = next_node
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and maze[ny][nx].terrain_type == "path":
                    new_cost = cost_so_far[current] + 1
                    if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                        cost_so_far[next_node] = new_cost
                        priority = new_cost + self.heuristic(target, next_node)
                        heapq.heappush(frontier, (priority, next_node))
                        came_from[next_node] = current
                        
        if target not in came_from:
            return []
            
        path = []
        curr = target
        while curr is not None:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
        return path

class Boss:
    def __init__(self, start_pos, move_cooldown, color):
        self.pos = list(start_pos)
        self.move_cooldown = move_cooldown
        self.color = color
        self.last_move_time = pygame.time.get_ticks()
        self.path = []
        self.transition = [
            [10, 2, 5, 5], 
            [2, 10, 5, 5], 
            [5, 5, 10, 2], 
            [5, 5, 2, 10]]
        self.avg_accuracy = [1, 1]
        self.recency_bias = .8

    def update_transition(self, last_player_move, current_player_move):
        trans_dict = {"up": 0, "down": 1, "left": 2, "right": 3}
        self.avg_accuracy[0] *= self.recency_bias
        self.avg_accuracy[1] *= self.recency_bias
        if (random.choices([0, 1, 2, 3], weights=self.transition[trans_dict[last_player_move]])[0] == trans_dict[current_player_move]):
            self.avg_accuracy[0] += 1
        self.avg_accuracy[1] += 1
        last_move_idx = trans_dict[last_player_move]
        current_move_idx = trans_dict[current_player_move]
        for i in range(4):
            self.transition[last_move_idx][i] *= self.recency_bias
        self.transition[last_move_idx][current_move_idx] += 1

    def ambush(self, current_time, maze, player_pos, last_player_move):
        trans_dict = {"up": 0, "down": 1, "left": 2, "right": 3}
        move_dict = {0: (0, -1), 1: (0, 1), 2: (-1, 0), 3: (1, 0)}
        next_move = trans_dict[last_player_move]
        target = player_pos
        if self.heuristic(tuple(self.pos), tuple(player_pos)) < 5:
            lookahead = 0
        elif self.heuristic(tuple(self.pos), tuple(player_pos)) < 10:
            lookahead = 2
        elif self.heuristic(tuple(self.pos), tuple(player_pos)) < 20:
            lookahead = 5
        else:
            lookahead = 10
        for i in range(lookahead):
            curr_row = self.transition[next_move]
            filtered = []
            for i in range(4):
                dx, dy = move_dict[i]
                new_x = target[0] + dx
                new_y = target[1] + dy
                if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE and maze[new_y][new_x].terrain_type == "path":
                    filtered.append((curr_row[i], (new_x, new_y)))
                else:
                    filtered.append((0, (new_x, new_y)))
            if filtered:
                next_move = random.choices([i for i in range(4)], weights=[f[0] for f in filtered])[0]
                target = filtered[next_move][1]
        self.move(current_time, maze, target)

    def update_path(self, maze, target_pos):
        self.path = self.get_astar_path(maze, tuple(self.pos), tuple(target_pos))

    def move(self, current_time, maze, player_pos):
        if current_time - self.last_move_time > self.move_cooldown:
            self.update_path(maze, player_pos)
            if len(self.path) > 1:
                if tuple(self.pos) in self.path:
                    idx = self.path.index(tuple(self.pos))
                    if idx + 1 < len(self.path):
                        self.pos = list(self.path[idx + 1])
                else:
                    self.pos = list(self.path[0])

            self.update_path(maze, player_pos)
            self.last_move_time = current_time

    def draw(self, screen):
        b_rect = pygame.Rect(self.pos[0] * CELL_SIZE + 4, self.pos[1] * CELL_SIZE + 4, CELL_SIZE - 8, CELL_SIZE - 8)
        pygame.draw.rect(screen, self.color, b_rect, border_radius=4)

    def draw_path(self, screen):
        for step in self.path:
            if list(step) != self.pos:
                center_x = step[0] * CELL_SIZE + CELL_SIZE // 2
                center_y = step[1] * CELL_SIZE + CELL_SIZE // 2
                pygame.draw.circle(screen, self.color, (center_x, center_y), CELL_SIZE // 12)

    def draw_label(self, screen):
        font = pygame.font.SysFont(None, CELL_SIZE // 2)
        label = font.render(str(round(self.avg_accuracy[0] / self.avg_accuracy[1] * 100)) + "%", True, (255, 255, 255))
        screen.blit(label, (self.pos[0] * CELL_SIZE + 5, self.pos[1] * CELL_SIZE - 10))

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_astar_path(self, maze, start, target):
        if start == target:
            return [start]
    
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}
        
        while frontier:
            _, current = heapq.heappop(frontier)
            if current == target:
                break
                
            cx, cy = current
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                next_node = (cx + dx, cy + dy)
                nx, ny = next_node
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and maze[ny][nx].terrain_type == "path":
                    new_cost = cost_so_far[current] + 1
                    if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                        cost_so_far[next_node] = new_cost
                        priority = new_cost + self.heuristic(target, next_node)
                        heapq.heappush(frontier, (priority, next_node))
                        came_from[next_node] = current
                    
        if target not in came_from:
            return []
            
        path = []
        curr = target
        while curr is not None:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
        return path


maze = generate_maze(GRID_SIZE, .25)

player = Player(start_pos=[GRID_SIZE - 4, GRID_SIZE - 4], move_cooldown=150, color=(52, 152, 219))
maze[player.pos[1]][player.pos[0]].terrain_type = "path"

ghosts = [
    Ghost(start_pos=(1, 1), move_cooldown=220, color=(231, 76, 60)),
    Ghost(start_pos=(1, 3), move_cooldown=220, color=(243, 156, 18))
]

boss = Boss(start_pos=(GRID_SIZE - 2, 1), move_cooldown=300, color=(155, 89, 182))

for ghost in ghosts:
    maze[ghost.pos[1]][ghost.pos[0]].terrain_type = "path"

PLAYER_COOLDOWN = 150
last_player_move_time = pygame.time.get_ticks()

# --- MAIN GAME LOOP ---
debug = False
running = True
last_player_move = "up"
while running:
    current_time = pygame.time.get_ticks()
    
    # 1. Event Handling
    dx, dy = 0, 0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_F1:
                debug = not debug
            
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        dy = -1
    elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
        dy = 1
    elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
        dx = -1
    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        dx = 1

    # 2. Update Positions
    if (dx != 0 or dy != 0) and (current_time - last_player_move_time > PLAYER_COOLDOWN):
        new_px = player.pos[0] + dx
        new_py = player.pos[1] + dy

        if dx == 1:
            new_last_player_move = "right"
        elif dx == -1:
            new_last_player_move = "left"
        elif dy == 1:
            new_last_player_move = "down"
        elif dy == -1:
            new_last_player_move = "up"

        boss.update_transition(last_player_move, new_last_player_move)
        last_player_move = new_last_player_move
        
        if 0 <= new_px < GRID_SIZE and 0 <= new_py < GRID_SIZE and maze[new_py][new_px].terrain_type == "path":
            player.pos = [new_px, new_py]
            last_player_move_time = current_time

    for ghost in ghosts:
        ghost.update_state(player.pos)
    boss.ambush(current_time, maze, player.pos, last_player_move)

    for ghost in ghosts:
        if player.pos == ghost.pos:
            print("Game Over! You got cornered by the AI.")
            running = False
    if player.pos == boss.pos:
        print("Game Over! You got cornered by the Boss.")
        running = False

    # 3. Rendering Layers
    screen.fill(COLOR_BG)
    
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if maze[row][col].terrain_type == "wall":
                pygame.draw.rect(screen, COLOR_WALL, rect)
   
    for ghost in ghosts:
        ghost.draw(screen)
        if debug:
            ghost.draw_path(screen)
            ghost.draw_label(screen)

    if debug:
        boss.draw_path(screen)
        boss.draw_label(screen)
    boss.draw(screen)

    p_rect = pygame.Rect(player.pos[0] * CELL_SIZE + 4, player.pos[1] * CELL_SIZE + 4, CELL_SIZE - 8, CELL_SIZE - 8)
    pygame.draw.rect(screen, COLOR_PLAYER, p_rect, border_radius=4)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()
