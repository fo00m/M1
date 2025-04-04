import pygame
import pandas as pd
import tkinter as tk
from tkinter import filedialog, simpledialog
from pyproj import Transformer, CRS
import sys
import datetime
import os
from PIL import Image, ImageSequence  # For GIF support

# Constants
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
FPS = 60
OCEAN_COLOR = (20, 40, 100)
PROGRESS_BAR_HEIGHT = 20
BUTTON_WIDTH = 150
BUTTON_HEIGHT = 40
MARGIN = 10
GRID_COLOR = (255, 255, 255, 220)  # Brighter white with high opacity
GRID_LABEL_COLOR = (255, 255, 0)  # Yellow for better visibility
GRID_LINE_WIDTH = 2  # Thicker lines
UI_BG_COLOR = (40, 40, 40)  # Dark gray for UI elements
UI_TEXT_COLOR = (255, 255, 255)  # White text

SPEED_INCREMENT = 0.1
MIN_SPEED = 0.1
MAX_SPEED = 5.0
DEFAULT_SPEED = 1.0

# Initialize Tkinter
root = tk.Tk()
root.withdraw()

class AnimatedBackground:
    def __init__(self, gif_path):
        self.frames = []
        self.current_frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_delay = 100  # ms
        
        # Load GIF using PIL
        pil_image = Image.open(gif_path)
        for frame in ImageSequence.Iterator(pil_image):
            frame = frame.convert("RGBA")
            pygame_image = pygame.image.fromstring(
                frame.tobytes(), frame.size, frame.mode
            ).convert_alpha()
            self.frames.append(pygame.transform.scale(
                pygame_image, (WINDOW_WIDTH, WINDOW_HEIGHT)
            ))
    
    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_delay:
            self.last_update = now
            self.current_frame = (self.current_frame + 1) % len(self.frames)
    
    def get_current_frame(self):
        return self.frames[self.current_frame]

def prompt_manual_column_selection(df):
    col_names = df.columns.tolist()
    col_str = "\n".join([f"{i + 1}. {col}" for i, col in enumerate(col_names)])

    x_col_num = simpledialog.askstring("Manual Column Selection", f"Enter number for X (Longitude) column:\n{col_str}")
    y_col_num = simpledialog.askstring("Manual Column Selection", f"Enter number for Y (Latitude) column:\n{col_str}")
    t_col_num = simpledialog.askstring("Manual Column Selection", f"Enter number for Time column:\n{col_str}")
    id_col_num = simpledialog.askstring("Manual Column Selection", f"Enter number for ID column (optional, leave blank for default):\n{col_str}")

    try:
        x_col = col_names[int(x_col_num) - 1]
        y_col = col_names[int(y_col_num) - 1]
        t_col = col_names[int(t_col_num) - 1]
        id_col = col_names[int(id_col_num) - 1] if id_col_num else None
    except (ValueError, IndexError):
        sys.exit("Invalid input for column selection.")

    return x_col, y_col, t_col, id_col

def load_and_process_csv():
    file_path = filedialog.askopenfilename(title="Select CSV", filetypes=[("CSV Files", "*.csv")])
    if not file_path:
        sys.exit("No file selected.")

    df = pd.read_csv(file_path)
    x_col, y_col, t_col, id_col = prompt_manual_column_selection(df)
    df = df.dropna(subset=[x_col, y_col, t_col])
    df[t_col] = pd.to_datetime(df[t_col])

    projection_input = simpledialog.askstring("Projection", "Enter projection (e.g., EPSG:4326)", initialvalue="EPSG:4326")
    transformer = Transformer.from_crs(CRS(projection_input), CRS("EPSG:4326"), always_xy=True)
    df['lon'], df['lat'] = zip(*df.apply(lambda row: transformer.transform(row[x_col], row[y_col]), axis=1))
    df['timestamp'] = df[t_col]

    if id_col:
        df['id'] = df[id_col]
    else:
        df['id'] = 0

    return df

def latlon_to_screen(lat, lon, zoom_level=1.0, center_lat=None, center_lon=None):
    if center_lat is None or center_lon is None:
        center_lat = lat
        center_lon = lon
    
    x = (lon - center_lon) * (WINDOW_WIDTH / 360) * zoom_level + WINDOW_WIDTH // 2
    y = (center_lat - lat) * (WINDOW_HEIGHT / 180) * zoom_level + WINDOW_HEIGHT // 2
    
    return int(x), int(y)

def load_background():
    file_path = filedialog.askopenfilename(
        title="Select Background Image/GIF", 
        filetypes=[("Image Files", "*.png *.jpg *.jpeg"), ("GIF Files", "*.gif")]
    )
    if not file_path:
        sys.exit("No background selected.")
    
    if file_path.lower().endswith('.gif'):
        return AnimatedBackground(file_path)
    else:
        image = pygame.image.load(file_path)
        return pygame.transform.scale(image, (WINDOW_WIDTH, WINDOW_HEIGHT))

def draw_progress_bar(screen, current_time, min_time, max_time, font, current_speed):
    total_duration = (max_time - min_time).total_seconds()
    elapsed = (current_time - min_time).total_seconds()
    progress = max(0.0, min(1.0, elapsed / total_duration))

    progress_width = int(WINDOW_WIDTH * progress)
    pygame.draw.rect(screen, (100, 200, 100), (0, WINDOW_HEIGHT - PROGRESS_BAR_HEIGHT, progress_width, PROGRESS_BAR_HEIGHT))
    pygame.draw.rect(screen, (255, 255, 255), (0, WINDOW_HEIGHT - PROGRESS_BAR_HEIGHT, WINDOW_WIDTH, PROGRESS_BAR_HEIGHT), 2)

    # Create background for all labels
    bg_height = 90
    bg_surface = pygame.Surface((WINDOW_WIDTH, bg_height))
    bg_surface.fill(UI_BG_COLOR)
    screen.blit(bg_surface, (0, WINDOW_HEIGHT - PROGRESS_BAR_HEIGHT - bg_height))

    min_label = font.render(min_time.strftime('%Y-%m-%d %H:%M:%S'), True, UI_TEXT_COLOR)
    max_label = font.render(max_time.strftime('%Y-%m-%d %H:%M:%S'), True, UI_TEXT_COLOR)
    current_label = font.render(current_time.strftime('%Y-%m-%d %H:%M:%S'), True, UI_TEXT_COLOR)
    speed_label = font.render(f"Speed: {current_speed:.1f}x", True, UI_TEXT_COLOR)

    screen.blit(min_label, (MARGIN, WINDOW_HEIGHT - PROGRESS_BAR_HEIGHT - 30))
    screen.blit(max_label, (WINDOW_WIDTH - max_label.get_width() - MARGIN, WINDOW_HEIGHT - PROGRESS_BAR_HEIGHT - 30))
    screen.blit(current_label, ((WINDOW_WIDTH - current_label.get_width()) // 2, WINDOW_HEIGHT - PROGRESS_BAR_HEIGHT - 30))
    screen.blit(speed_label, ((WINDOW_WIDTH - speed_label.get_width()) // 2, WINDOW_HEIGHT - PROGRESS_BAR_HEIGHT - 60))

    # Centered reset button between - and + buttons
    draw_button(screen, "-", WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT - PROGRESS_BAR_HEIGHT - 100, 30, 30, (150, 50, 50), font)
    draw_button(screen, "Reset", WINDOW_WIDTH // 2 - 30, WINDOW_HEIGHT - PROGRESS_BAR_HEIGHT - 100, 60, 30, (100, 100, 100), font)
    draw_button(screen, "+", WINDOW_WIDTH // 2 + 50, WINDOW_HEIGHT - PROGRESS_BAR_HEIGHT - 100, 30, 30, (50, 150, 50), font)

def draw_button(screen, text, x, y, width, height, color, font):
    pygame.draw.rect(screen, color, (x, y, width, height))
    label = font.render(text, True, (255, 255, 255))
    screen.blit(label, (x + (width - label.get_width()) // 2, y + (height - label.get_height()) // 2))

def calculate_bounding_box(grouped_paths):
    min_lat = float('inf')
    max_lat = -float('inf')
    min_lon = float('inf')
    max_lon = -float('inf')
    
    for track_id, points in grouped_paths.items():
        for point in points:
            min_lat = min(min_lat, point.lat)
            max_lat = max(max_lat, point.lat)
            min_lon = min(min_lon, point.lon)
            max_lon = max(max_lon, point.lon)
    
    return min_lat, max_lat, min_lon, max_lon

def calculate_active_center(current_positions):
    if not current_positions:
        return None, None
    
    sum_lat = 0
    sum_lon = 0
    count = 0
    
    for track_id, row in current_positions.items():
        sum_lat += row.lat
        sum_lon += row.lon
        count += 1
    
    return sum_lat / count, sum_lon / count

def calculate_auto_zoom(current_positions, grouped_paths):
    if not current_positions:
        return 1.0
    
    # Calculate bounding box of active points
    min_lat = min(p.lat for p in current_positions.values())
    max_lat = max(p.lat for p in current_positions.values())
    min_lon = min(p.lon for p in current_positions.values())
    max_lon = max(p.lon for p in current_positions.values())
    
    # Add 25% padding to ensure all points are visible
    lat_span = (max_lat - min_lat) * 1.25
    lon_span = (max_lon - min_lon) * 1.25
    
    # Calculate required zoom level to fit all active points
    zoom_lat = 180 / lat_span if lat_span != 0 else 1.0
    zoom_lon = 360 / lon_span if lon_span != 0 else 1.0
    return min(zoom_lat, zoom_lon, 20.0)  # Limit max zoom to 20x

def draw_grid(screen, font, zoom_level, center_lat, center_lon):
    # Calculate appropriate grid spacing based on zoom level
    base_spacing = max(0.5, 20 / zoom_level)  # More spaced out grid lines
    
    # Round to nearest nice interval
    intervals = [0.5, 1, 2, 5, 10, 15, 30, 45, 90]
    grid_spacing = min(intervals, key=lambda x: abs(x - base_spacing))
    
    # Calculate visible bounds with some padding
    visible_width_deg = 360 / zoom_level
    visible_height_deg = 180 / zoom_level
    west = center_lon - visible_width_deg/2
    east = center_lon + visible_width_deg/2
    south = center_lat - visible_height_deg/2
    north = center_lat + visible_height_deg/2
    
    # Draw every other longitude line (vertical)
    lon = int(west / grid_spacing) * grid_spacing
    while lon <= east + grid_spacing:
        x, _ = latlon_to_screen(0, lon, zoom_level, center_lat, center_lon)
        if -50 <= x <= WINDOW_WIDTH + 50:
            pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT), GRID_LINE_WIDTH)
            # Show labels at both top and bottom
            label_text = f"{abs(lon):.1f}°{'W' if lon < 0 else 'E'}"
            label = font.render(label_text, True, GRID_LABEL_COLOR)
            screen.blit(label, (x + 4, 4))  # Top label
            screen.blit(label, (x + 4, WINDOW_HEIGHT - label.get_height() - 4))  # Bottom label
        lon += grid_spacing * 2  # Skip every other line
    
    # Draw every other latitude line (horizontal)
    lat = int(south / grid_spacing) * grid_spacing
    while lat <= north + grid_spacing:
        _, y = latlon_to_screen(lat, 0, zoom_level, center_lat, center_lon)
        if -50 <= y <= WINDOW_HEIGHT + 50:
            pygame.draw.line(screen, GRID_COLOR, (0, y), (WINDOW_WIDTH, y), GRID_LINE_WIDTH)
            # Show labels at both left and right
            label_text = f"{abs(lat):.1f}°{'S' if lat < 0 else 'N'}"
            label = font.render(label_text, True, GRID_LABEL_COLOR)
            screen.blit(label, (4, y + 4))  # Left label
            screen.blit(label, (WINDOW_WIDTH - label.get_width() - 4, y + 4))  # Right label
        lat += grid_spacing * 2  # Skip every other line

def main():
    df = load_and_process_csv()
    grouped_paths = {}
    colors = {}
    current_positions = {}
    color_palette = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255)]

    for i, (track_id, group) in enumerate(df.groupby("id")):
        group = group.sort_values("timestamp")
        grouped_paths[track_id] = list(group.itertuples(index=False))
        colors[track_id] = color_palette[i % len(color_palette)]

    min_time = df['timestamp'].min()
    max_time = df['timestamp'].max()
    current_time = min_time
    speed = DEFAULT_SPEED

    selected_ids = set()
    hide_non_selected = False  # Changed from show_all to hide_non_selected

    time_step_mode = 'hour'
    def get_time_step():
        if time_step_mode == 'hour': return datetime.timedelta(hours=speed)
        if time_step_mode == 'day': return datetime.timedelta(days=speed)
        if time_step_mode == 'month': return datetime.timedelta(days=30 * speed)

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Centered Geospatial Animation with Grid")
    font = pygame.font.SysFont('Arial', 16, bold=True)
    small_font = pygame.font.SysFont('Arial', 14)
    clock = pygame.time.Clock()

    paused = False
    show_trail = True
    background = load_background()
    background_is_gif = isinstance(background, AnimatedBackground)
    
    zoom_level = 1.0
    auto_zoom = True  # Start with auto-zoom enabled by default

    while True:
        screen.fill(OCEAN_COLOR)
        
        # Draw background (static image or animated GIF)
        if background_is_gif:
            background.update()
            screen.blit(background.get_current_frame(), (0, 0))
        else:
            screen.blit(background, (0, 0))
        
        # Calculate center of active points
        center_lat, center_lon = calculate_active_center(current_positions)
        if center_lat is None or center_lon is None:
            center_lat, center_lon = 0, 0  # Default center if no points
        
        # Auto-adjust zoom if needed to keep all points visible
        if auto_zoom and current_positions:
            zoom_level = calculate_auto_zoom(current_positions, grouped_paths)
        
        # Draw the grid with labels on all sides
        draw_grid(screen, font, zoom_level, center_lat, center_lon)

        mouse_pos = pygame.mouse.get_pos()
        geo_lon = (mouse_pos[0] - WINDOW_WIDTH // 2) / (WINDOW_WIDTH / 360) / zoom_level + center_lon
        geo_lat = center_lat - (mouse_pos[1] - WINDOW_HEIGHT // 2) / (WINDOW_HEIGHT / 180) / zoom_level
        
        # Draw unified UI panel in top-left corner
        panel_width = 220
        panel_height = 100 + len(selected_ids) * 20
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.fill(UI_BG_COLOR)
        screen.blit(panel_surface, (10, 10))
        
        # Mouse coordinates
        coord_label = font.render(f"Lat: {geo_lat:.4f}", True, UI_TEXT_COLOR)
        screen.blit(coord_label, (20, 20))
        coord_label2 = font.render(f"Lon: {geo_lon:.4f}", True, UI_TEXT_COLOR)
        screen.blit(coord_label2, (20, 40))
        
        # Selected IDs legend
        y_offset = 70
        selected_label = font.render("Selected IDs:", True, UI_TEXT_COLOR)
        screen.blit(selected_label, (20, y_offset))
        
        for i, sid in enumerate(sorted(selected_ids)):
            color = colors[sid]
            pygame.draw.circle(screen, color, (20 + 6, y_offset + 20 * (i + 1) + 6), 6)
            id_label = small_font.render(str(sid), True, UI_TEXT_COLOR)
            screen.blit(id_label, (35, y_offset + 20 * (i + 1)))

        # Draw trails and points
        for track_id, points in grouped_paths.items():
            if hide_non_selected and track_id not in selected_ids:
                continue
            prev = None
            for row in points:
                if row.timestamp <= current_time:
                    if show_trail and prev:
                        px, py = latlon_to_screen(prev.lat, prev.lon, zoom_level, center_lat, center_lon)
                        cx, cy = latlon_to_screen(row.lat, row.lon, zoom_level, center_lat, center_lon)
                        pygame.draw.line(screen, colors[track_id], (px, py), (cx, cy), 2)
                    current_positions[track_id] = row
                    prev = row

        for track_id, row in current_positions.items():
            if hide_non_selected and track_id not in selected_ids:
                continue
            x, y = latlon_to_screen(row.lat, row.lon, zoom_level, center_lat, center_lon)
            circle = pygame.draw.circle(screen, colors[track_id], (x, y), 5)
            if track_id in selected_ids:
                pygame.draw.circle(screen, (255, 255, 255), (x, y), 8, 2)
            if circle.collidepoint(mouse_pos):
                if pygame.mouse.get_pressed()[0]:
                    if track_id in selected_ids:
                        selected_ids.remove(track_id)
                    else:
                        selected_ids.add(track_id)

        draw_progress_bar(screen, current_time, min_time, max_time, font, speed)

        draw_button(screen, "Pause", WINDOW_WIDTH - BUTTON_WIDTH - 10, 10, BUTTON_WIDTH, BUTTON_HEIGHT, (50, 150, 50), font)
        draw_button(screen, "Replay", WINDOW_WIDTH - BUTTON_WIDTH - 10, 60, BUTTON_WIDTH, BUTTON_HEIGHT, (50, 150, 50), font)
        draw_button(screen, "Toggle Trail", WINDOW_WIDTH - BUTTON_WIDTH - 10, 110, BUTTON_WIDTH, BUTTON_HEIGHT, (100, 100, 200), font)
        draw_button(screen, f"Time: {time_step_mode.title()}", WINDOW_WIDTH - BUTTON_WIDTH - 10, 160, BUTTON_WIDTH, BUTTON_HEIGHT, (150, 100, 50), font)
        # Changed from "Show All" to "Hide Non-Selected"
        hide_button_text = "Show All" if hide_non_selected else "Hide Non-Selected"
        draw_button(screen, hide_button_text, WINDOW_WIDTH - BUTTON_WIDTH - 10, 210, BUTTON_WIDTH, BUTTON_HEIGHT, (180, 80, 100), font)
        zoom_button_text = "Auto-Zoom: ON" if auto_zoom else "Auto-Zoom: OFF"
        draw_button(screen, zoom_button_text, WINDOW_WIDTH - BUTTON_WIDTH - 10, 260, BUTTON_WIDTH, BUTTON_HEIGHT, (80, 100, 180), font)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if WINDOW_WIDTH // 2 - 100 <= x <= WINDOW_WIDTH // 2 - 70 and WINDOW_HEIGHT - PROGRESS_BAR_HEIGHT - 100 <= y <= WINDOW_HEIGHT - PROGRESS_BAR_HEIGHT - 70:
                    speed = max(MIN_SPEED, speed - SPEED_INCREMENT)
                elif WINDOW_WIDTH // 2 + 50 <= x <= WINDOW_WIDTH // 2 + 80 and WINDOW_HEIGHT - PROGRESS_BAR_HEIGHT - 100 <= y <= WINDOW_HEIGHT - PROGRESS_BAR_HEIGHT - 70:
                    speed = min(MAX_SPEED, speed + SPEED_INCREMENT)
                elif WINDOW_WIDTH // 2 - 30 <= x <= WINDOW_WIDTH // 2 + 30 and WINDOW_HEIGHT - PROGRESS_BAR_HEIGHT - 100 <= y <= WINDOW_HEIGHT - PROGRESS_BAR_HEIGHT - 70:
                    speed = DEFAULT_SPEED
                elif WINDOW_WIDTH - BUTTON_WIDTH - 10 <= x <= WINDOW_WIDTH - 10:
                    if 10 <= y <= 10 + BUTTON_HEIGHT:
                        paused = not paused
                    elif 60 <= y <= 60 + BUTTON_HEIGHT:
                        current_time = min_time
                        current_positions.clear()
                        paused = False
                    elif 110 <= y <= 110 + BUTTON_HEIGHT:
                        show_trail = not show_trail
                    elif 160 <= y <= 160 + BUTTON_HEIGHT:
                        if time_step_mode == 'hour': time_step_mode = 'day'
                        elif time_step_mode == 'day': time_step_mode = 'month'
                        else: time_step_mode = 'hour'
                    elif 210 <= y <= 210 + BUTTON_HEIGHT:
                        hide_non_selected = not hide_non_selected  # Toggle hide non-selected
                    elif 260 <= y <= 260 + BUTTON_HEIGHT:
                        auto_zoom = not auto_zoom
                        if auto_zoom and current_positions:
                            zoom_level = calculate_auto_zoom(current_positions, grouped_paths)

            elif event.type == pygame.MOUSEWHEEL:
                if not auto_zoom:  # Only allow manual zoom when auto-zoom is off
                    zoom_change = 1.1 if event.y > 0 else 0.9
                    new_zoom = zoom_level * zoom_change
                    zoom_level = max(1.0, min(20.0, new_zoom))

        if not paused:
            current_time += get_time_step()
            if current_time > max_time:
                current_time = max_time

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()