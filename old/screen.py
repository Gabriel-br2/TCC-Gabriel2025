import base64
import datetime
import os
import shutil
import sys

import pygame
import pymunk.pygame_util


class Screen:
    """
    Manages the Pygame screen, physics simulation, and screenshot functionality.
    """

    def __init__(
        self, config, color, click_callback, client_id, player_color, debug=False
    ):
        """
        Initializes the Screen object.

        Args:
            config (dict): Configuration data.
            color (dict): Color data.
            click_callback (function): Callback function for key presses.
            client_id (int): The client's ID.
            player_color (str): The player's color.
            debug (bool, optional): Debug mode. Defaults to False.
        """
        pygame.init()  # Initialize Pygame

        self.menu_running = True  # Flag for menu loop (currently unused).
        self.game_running = True  # Flag for game loop.
        self.debug = debug  # Debug mode.
        self.color = color  # Color dictionary.
        self.config = config  # Configuration dictionary.
        self.click_callback = click_callback  # Callback for key presses.

        self.screen_height = config["screen"]["height"]  # Screen height from config.
        self.screen_width = config["screen"]["width"]  # Screen width from config.

        self.transparency = config["game"]["transparency"]

        self.clock = pygame.time.Clock()  # Pygame clock for controlling frame rate.
        self.space = pymunk.Space()  # Create a Pymunk physics space.

        self.space.gravity = (0, 0)  # Set gravity to zero (no gravity).
        self.fps = 60  # Frames per second.

        self.font = pygame.font.SysFont(
            "Arial", 18, bold=True
        )  # Font for displaying text.

        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height)
        )  # Create the Pygame screen.
        pygame.display.set_caption(
            f"{config['screen']['caption']} - player: {client_id} - {player_color}"
        )  # Set window title.
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)

    def screenshot_base64(self, save=False, file_path="screenshot/"):
        """
        Captures a screenshot and optionally saves it as a PNG and Base64 encoded text file.

        Args:
            save (bool, optional): Whether to save the screenshot to a file. Defaults to False.
            file_path (str, optional): The directory to save the screenshot. Defaults to 'screenshot/'.

        Returns:
            bytes: The Base64 encoded screenshot data.
        """
        now = datetime.datetime.now()  # Get current time for filename.
        timestamp = now.strftime("%Y%m%d_%H%M%S")  # Format timestamp.
        file_name = f"{file_path}{timestamp}"  # Create filename.

        pygame.image.save(self.screen, f"{file_name}.png")  # Save screenshot as PNG.

        with open(f"{file_name}.png", "rb") as f:  # Open PNG file.
            base64_string = base64.b64encode(f.read())  # Encode to Base64.

        if save:  # If saving is enabled.
            target_dir = f"{file_path}{timestamp}/"  # Create timestamped directory.
            os.makedirs(target_dir)  # Create the directory.

            dest_png = os.path.join(
                target_dir, os.path.basename(f"{file_name}.png")
            )  # Path for PNG copy.
            shutil.copy(
                f"{file_name}.png", dest_png
            )  # Copy PNG to timestamped directory.

            dest_txt = os.path.join(
                target_dir, os.path.basename(f"{file_name}.txt")
            )  # Path for Base64 text file.
            with open(dest_txt, "w") as f:  # Open text file.
                f.write(
                    base64_string.decode("utf-8")
                )  # Write Base64 data to text file.

        os.remove(f"{file_name}.png")  # Remove original PNG.
        return base64_string  # Return Base64 data.

    def game_loop(
        self,
        set_new_position,
        get_new_position,
        client_socket,
        objects,
        player_id,
        iou,
        playerType,
    ):
        """
        Runs the main game loop.

        Args:
            set_new_position (function): Function to send updated positions to the server.
            get_new_position (function): Function to receive updated positions from the server.
            client_socket (socket): The client socket.
            objects (dict): Dictionary of game objects.
            player_id (int): The player's ID.
            iou (float): The Intersection over Union (IoU) value.
            playertype (str): The player is a llm or a human.

        Returns:
            None
        """
        for event in pygame.event.get():  # Handle events.
            if event.type == pygame.QUIT:  # If player quits.
                self.game_running = False  # Set game loop flag to false.
            if event.type == pygame.KEYDOWN:  # If a key is pressed.
                self.click_callback(event.key)  # Call the click callback function.

        self.screen.fill(
            self.color["background"]
        )  # Fill the screen with the background color.
        self.space.step(1 / self.fps)  # Step the physics simulation.

        # Draw other players' objects.
        for player_index in range(self.config["game"]["playerNum"]):
            if player_id != player_index:
                for obj in objects["you"][f"P{player_index}"]["pos"]:
                    objects[obj[3]].draw(
                        [
                            *self.color[objects["you"][f"P{player_index}"]["color"]],
                            self.transparency,
                        ],
                        obj[:2],
                        obj[2],
                    )

        if playerType == "human":
            new_pos = pygame.mouse.get_pos()  # Get mouse position.

        elif playerType == "LLM":
            new_pos = objects["me"][0].setPosition()

        objects["me"][
            0
        ].body.position = new_pos  # Set player's position to mouse position.
        objects["me"][0].draw()  # Draw the player.

        # Prepare updated position data to send to the server.
        updated_positions = []
        for obj in objects["me"]:
            x, y = obj.body.position
            updated_positions.append(
                [x, y, obj.body.angle, obj.type]
            )  # Store position, angle, and type
            obj.draw()  # Draw the objects

        new_position = updated_positions  # The updated positions to send
        set_new_position(
            client_socket, new_position
        )  # Send new position to the server.

        data = get_new_position(client_socket)  # Receive updated data from the server.
        for player_index in range(
            self.config["game"]["playerNum"]
        ):  # Update other players positions
            if player_id != player_index:
                objects["you"][f"P{player_index}"]["pos"] = data[f"P{player_index}"][
                    "pos"
                ]  # Update other players' positions.

        iou = data["IoU"]  # Get the IoU value from the server.
        iou_text = self.font.render(
            f"Objetivo Concluído: {iou * 100:.2f} %", True, (0, 0, 0)
        )  # Render the IoU text.
        text_rect = iou_text.get_rect(
            center=(self.config["screen"]["width"] // 2, 25)
        )  # Create text rectangle.
        self.screen.blit(iou_text, text_rect)  # Draw the IoU text.

        pygame.display.flip()  # Update the display.
        self.clock.tick(self.fps)  # Control frame rate.

    def close(self):
        """
        Closes the Pygame window and quits Pygame.
        """
        pygame.quit()  # Quit Pygame.
        sys.exit()  # Exit the program.
