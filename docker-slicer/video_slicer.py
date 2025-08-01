# video_slicer.py
import cv2
import os

def split_video_into_frames(video_path, output_folder):
    """
    Splits a video into its individual frames, displaying each frame and
    allowing the user to interrupt the process by pressing 'q'.

    Args:
        video_path (str): The full path to the input video file.
        output_folder (str): The path to the folder where the frames will be saved.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")

    video_capture = cv2.VideoCapture(video_path)
    if not video_capture.isOpened():
        print(f"Error: Could not open video file: {video_path}")
        return

    frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    print(f"\nVideo Properties:")
    print(f"  - Frame Count: {frame_count}")
    print(f"  - FPS: {fps}")

    print("\nSplitting video into frames...")
    print("Press 'q' or 'Q' on the video window to stop the process at any time.")

    cv2.namedWindow("Video Frame", cv2.WINDOW_NORMAL)

    current_frame = 0
    while True:
        success, frame = video_capture.read()
        if not success:
            print("\nEnd of video reached.")
            break

        cv2.imshow("Video Frame", frame)
        frame_filename = os.path.join(output_folder, f"frame_{current_frame:05d}.jpg")
        cv2.imwrite(frame_filename, frame)
        current_frame += 1

        if current_frame % 100 == 0 or current_frame == frame_count:
            print(f"  - Saved frame {current_frame}/{frame_count}")

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q'):
            print("\nExecution interrupted by user.")
            break

    video_capture.release()
    cv2.destroyAllWindows()
    print("\nVideo splitting process finished.")
    print(f"{current_frame} frames were saved in: {output_folder}")

if __name__ == "__main__":
    # Define shared data folders within the container
    input_video_dir = "/app/videos"
    output_frames_dir = "/app/frames"

    print("--- Video Slicer Docker App ---")
    print(f"Place your videos in the host directory mapped to {input_video_dir}")
    print(f"Frames will be saved in the host directory mapped to {output_frames_dir}\n")
    
    # Prompt the user for the video filename
    video_filename = input("Enter the filename of the video (must be in the 'videos' folder): ")
    video_file = os.path.join(input_video_dir, video_filename)

    if not os.path.isfile(video_file):
        print(f"Error: The video file '{video_filename}' was not found in the {input_video_dir} directory.")
    else:
        # Create a unique output folder for this video
        output_subfolder = os.path.splitext(video_filename)[0]
        output_dir = os.path.join(output_frames_dir, output_subfolder)
        
        split_video_into_frames(video_file, output_dir)
