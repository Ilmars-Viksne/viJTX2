import numpy as np
import cv2
import skimage.io
import skimage.color
import skimage.util
import torch
import micro_sam.util as util
import os
import glob
from tqdm import tqdm

# --- MODIFIED SECTION ---
# Define fixed I/O directories for the container.
# These paths will be mapped to the user's local machine via Docker volumes.
INPUT_DIR = "/input"
OUTPUT_DIR = "/output"
# --- END MODIFIED SECTION ---

class ImageHandler:
    """
    Handles loading, preparing, and displaying images.
    Can load single images or a sequence of frames from a folder.
    """
    def __init__(self):
        self.raw_image = None
        self.prepared_image = None
        self.height = 0
        self.width = 0
        self.title = ""
        self.image_paths = []

    def load_from_local_file(self, path: str) -> bool:
        """Loads a single image from a local file path. Returns True on success."""
        try:
            full_path = os.path.join(INPUT_DIR, path)
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"The file was not found at '{full_path}'. Make sure it is in your mapped input directory.")
            self.raw_image = skimage.io.imread(full_path)
            self.title = f"Loaded: {os.path.basename(path)}"
            print(f"Successfully loaded image from {full_path}")
            return True
        except Exception as e:
            print(f"An error occurred while loading the file: {e}")
            self.raw_image = None
            return False

    def load_from_folder(self, folder_name: str) -> bool:
        """Loads the first frame from a folder of images. Returns True on success."""
        try:
            folder_path = os.path.join(INPUT_DIR, folder_name)
            if not os.path.isdir(folder_path):
                raise NotADirectoryError(f"The path '{folder_path}' is not a valid directory inside the container.")
            
            self.image_paths = []
            extensions = ('*.png', '*.jpg', '*.jpeg', '*.tif', '*.tiff')
            for ext in extensions:
                self.image_paths.extend(glob.glob(os.path.join(folder_path, ext)))
            
            if not self.image_paths:
                print("No image files found in the specified folder.")
                return False

            self.image_paths.sort()
            self.raw_image = skimage.io.imread(self.image_paths[0])
            self.title = f"Loaded First Frame: {os.path.basename(self.image_paths[0])}"
            print(f"Found {len(self.image_paths)} frames. Loaded first frame for prompting.")
            return True
        except Exception as e:
            print(f"An error occurred while loading from the folder: {e}")
            self.image_paths = []
            self.raw_image = None
            return False

    @staticmethod
    def prepare_image(raw_image: np.ndarray) -> np.ndarray:
        """Prepares a raw image array for the SAM model (uint8, 3-channel RGB)."""
        image = raw_image
        if image.ndim == 2:
            image = skimage.color.gray2rgb(image)
        elif image.shape[2] == 4:
            image = skimage.color.rgba2rgb(image)
        if image.dtype != np.uint8:
            image = skimage.util.img_as_ubyte(image)
        return image

    def prepare_and_get_image(self) -> np.ndarray:
        """Prepares the loaded raw image and returns it."""
        if self.raw_image is None:
            raise RuntimeError("Cannot prepare image: No raw image has been loaded.")
        self.prepared_image = self.prepare_image(self.raw_image)
        self.height, self.width, _ = self.prepared_image.shape
        return self.prepared_image

    def show(self):
        """Displays the currently loaded raw image using OpenCV."""
        if self.raw_image is None:
            print("No image loaded.")
            return
        display_image = self.prepare_image(self.raw_image)
        display_image_bgr = cv2.cvtColor(display_image, cv2.COLOR_RGB2BGR)
        cv2.imshow(self.title, display_image_bgr)
        print("Image window is open. Press any key to close it and continue.")
        cv2.waitKey(0)
        cv2.destroyWindow(self.title)


class SegmentationModel:
    """
    Manages the SAM model for single-image prediction.
    """
    def __init__(self, model_type="vit_b_lm"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_type = model_type
        self.predictor = None
        self.is_image_set = False
        print(f"Using device: {self.device}")

    def initialize(self):
        """Initializes the SAM predictor."""
        if self.predictor is None:
            print(f"Initializing SAM predictor ({self.model_type})...")
            self.predictor = util.get_sam_model(model_type=self.model_type, device=self.device)
            print("Predictor initialized.")

    def set_image(self, image: np.ndarray, silent: bool = False):
        """Sets the image in the predictor to compute embeddings."""
        if self.predictor is None:
            raise RuntimeError("Model is not initialized. Call 'initialize()' first.")
        if not silent:
            print("Setting image in the predictor (computing embeddings)...")
        self.predictor.set_image(image)
        self.is_image_set = True
        if not silent:
            print("Embeddings computed and predictor is ready.")

    def predict_from_point(self, point_coords: np.ndarray):
        """Performs segmentation from a single point prompt."""
        if not self.is_image_set:
            raise RuntimeError("An image must be set before prediction. Call 'set_image()' first.")
        input_labels = np.array([1])
        masks, scores, _ = self.predictor.predict(
            point_coords=point_coords, point_labels=input_labels, multimask_output=True,
        )
        best_mask_idx = np.argmax(scores)
        final_mask = masks[best_mask_idx]
        best_score = scores[best_mask_idx]
        pixel_count = np.sum(final_mask)
        return final_mask, best_score, pixel_count


class InteractiveSegmenter:
    """
    Orchestrates the application, handling interactive segmentation and tracking.
    """
    def __init__(self, model_type="vit_b_lm"):
        self.image_handler = ImageHandler()
        self.model = SegmentationModel(model_type=model_type)

    def _visualize_segmentation(self, image, input_points, final_mask, score, pixel_count, title_suffix=""):
        """Displays the image with prompt and the resulting mask using OpenCV."""
        img1 = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        if input_points is not None:
            point_coords = (input_points[0, 0], input_points[0, 1])
            cv2.drawMarker(img1, point_coords, color=(0, 255, 0), markerType=cv2.MARKER_STAR, markerSize=40, thickness=2)
        cv2.putText(img1, f"Image with Prompt{title_suffix}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        img2 = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        color = np.array([255, 144, 30], dtype=np.uint8)
        mask_colored = np.zeros_like(img2, dtype=np.uint8)
        mask_colored[final_mask] = color
        img2 = cv2.addWeighted(img2, 1.0, mask_colored, 0.6, 0)
        info_text1 = f"Score: {score:.4f}"
        info_text2 = f"Pixels: {pixel_count}"
        cv2.putText(img2, info_text1, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(img2, info_text2, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(img2, "Segmentation Result", (10, img2.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        combined_image = np.hstack((img1, img2))
        window_title = "Segmentation Result"
        cv2.imshow(window_title, combined_image)
        print("Result window is open. Press any key to close it.")
        cv2.waitKey(0)
        cv2.destroyWindow(window_title)
    
    def _save_tracking_result(self, image, mask, score, pixel_count, output_path):
        """Saves a single frame of the tracking result with info text using OpenCV."""
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        color = np.array([255, 144, 30], dtype=np.uint8)
        mask_colored = np.zeros_like(image_bgr, dtype=np.uint8)
        mask_colored[mask] = color
        overlay = cv2.addWeighted(image_bgr, 1.0, mask_colored, 0.6, 0)
        info_text = f"Score: {score:.4f} | Pixels: {pixel_count}"
        cv2.putText(overlay, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imwrite(output_path, overlay)

    def _get_point_prompt(self):
        """Prompts user for a point and returns it."""
        while True:
            try:
                center_y, center_x = self.image_handler.height // 2, self.image_handler.width // 2
                x_input = input(f"Enter relative x coordinate (center is {center_x}): ")
                y_input = input(f"Enter relative y coordinate (center is {center_y}): ")
                relative_x, relative_y = int(x_input), int(y_input)
                abs_x = np.clip(center_x + relative_x, 0, self.image_handler.width - 1)
                abs_y = np.clip(center_y - relative_y, 0, self.image_handler.height - 1)
                input_points = np.array([[abs_x, abs_y]])
                print(f"Using prompt at: {input_points[0]} (relative: [{relative_x}, {relative_y}])")
                return input_points
            except ValueError:
                print("Invalid input. Please enter integers for coordinates.")

    def _run_tracking_session(self):
        """Runs the tracking workflow by re-segmenting each frame."""
        input_folder = input(f"Enter the name of the folder in '{INPUT_DIR}' with image frames: ")
        output_folder_name = input(f"Enter a name for the output folder in '{OUTPUT_DIR}': ")
        
        if not self.image_handler.load_from_folder(input_folder):
            return

        final_output_folder = os.path.join(OUTPUT_DIR, output_folder_name)
        os.makedirs(final_output_folder, exist_ok=True)
        
        prepared_first_frame = self.image_handler.prepare_and_get_image()
        self.image_handler.show()
        
        self.model.initialize()
        self.model.set_image(prepared_first_frame, silent=False)
        
        input_points = self._get_point_prompt()
        tracked_mask, score, pixel_count = self.model.predict_from_point(input_points)
        print(f"Initial mask found with {pixel_count} pixels. Score: {score:.4f}")
        self._visualize_segmentation(prepared_first_frame, input_points, tracked_mask, score, pixel_count, " (First Frame)")

        save_path = os.path.join(final_output_folder, os.path.basename(self.image_handler.image_paths[0]))
        self._save_tracking_result(prepared_first_frame, tracked_mask, score, pixel_count, save_path)
        
        remaining_frames = len(self.image_handler.image_paths) - 1
        if remaining_frames > 0:
            print(f"Starting tracking for the remaining {remaining_frames} frames...")
            for i in tqdm(range(1, len(self.image_handler.image_paths)), desc="Tracking Frames"):
                if np.sum(tracked_mask) == 0:
                    print(f"\nWarning: Object lost at frame {i-1}. Stopping track.")
                    break
                y_coords, x_coords = np.where(tracked_mask)
                center_y = int(y_coords.mean())
                center_x = int(x_coords.mean())
                new_prompt = np.array([[center_x, center_y]])
                frame_path = self.image_handler.image_paths[i]
                raw_next_frame = skimage.io.imread(frame_path)
                prepared_next_frame = self.image_handler.prepare_image(raw_next_frame)
                self.model.set_image(prepared_next_frame, silent=True)
                tracked_mask, score, pixel_count = self.model.predict_from_point(new_prompt)
                save_path = os.path.join(final_output_folder, os.path.basename(frame_path))
                self._save_tracking_result(prepared_next_frame, tracked_mask, score, pixel_count, save_path)
        print(f"\nTracking complete. Results saved in '{final_output_folder}'.")

    def _run_interactive_session(self):
        """Runs the workflow for interactively segmenting a single image."""
        prepared_image = None
        while prepared_image is None:
            path = input(f"Enter the name of your image file in '{INPUT_DIR}': ")
            success = self.image_handler.load_from_local_file(path)
            if success:
                prepared_image = self.image_handler.prepare_and_get_image()
            else:
                print("Image loading failed. Please try again.")
        
        self.image_handler.show()
        self.model.initialize()
        self.model.set_image(prepared_image, silent=False)

        while True:
            try:
                prompt = input("Enter relative coordinates or 'q' to quit (e.g. '10 20' or 'q'): ")
                if prompt.lower() == 'q': break
                parts = prompt.split()
                if len(parts) != 2: raise ValueError("Please provide two numbers for x and y.")
                relative_x, relative_y = int(parts[0]), int(parts[1])
                center_y, center_x = self.image_handler.height // 2, self.image_handler.width // 2
                abs_x = np.clip(center_x + relative_x, 0, self.image_handler.width - 1)
                abs_y = np.clip(center_y - relative_y, 0, self.image_handler.height - 1)
                input_points = np.array([[abs_x, abs_y]])
                print(f"Using prompt at: {input_points[0]} (relative: [{relative_x}, {relative_y}])")
                final_mask, score, pixel_count = self.model.predict_from_point(input_points)
                print(f"Mask generated with {pixel_count} pixels. Score: {score:.4f}")
                self._visualize_segmentation(prepared_image, input_points, final_mask, score, pixel_count)
            except ValueError as e:
                print(f"Invalid input: {e}. Please enter two integers or 'q'.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

    def run(self):
        """Starts the application by asking the user for the desired workflow."""
        print("Welcome to the Interactive Segmenter and Tracker!")
        while True:
            print("\n" + "="*30)
            print("Choose your workflow:")
            print("1. Interactively segment a single image")
            print("2. Track object in a folder of frames")
            print("q. Quit")
            print("="*30)
            choice = input("Enter your choice (1, 2, or q): ")
            if choice == '1':
                self._run_interactive_session()
            elif choice == '2':
                self._run_tracking_session()
            elif choice.lower() == 'q':
                break
            else:
                print("Invalid choice. Please try again.")
        print("Exiting program.")

if __name__ == "__main__":
    app = InteractiveSegmenter()
    app.run()
