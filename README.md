# Space Triage

**Space Triage** is a voice-guided ultrasound analysis system developed for astronauts operating in microgravity environments. The system integrates real-time image segmentation and diagnostic assessment to ensure that the correct anatomical area is captured during an ultrasound examination using the NASA Ultrasound-2 system. If the image does not display the desired area, Space Triage provides clear, step-by-step voice instructions to help reposition the probe and capture the correct view.

## Features

- **Voice-Activated Area Specification:**  
  Astronauts can use voice commands to specify the anatomical area they want to analyze (e.g., "Analyze the heart" or "Check the liver").

- **Ultrasound Image Input:**  
  The system accepts ultrasound images from the NASA Ultrasound-2 probe, captured in a microgravity environment.

- **Image Segmentation and Analysis:**  
  A trained segmentation model evaluates the input image to determine if the target anatomical area is visible.
  
- **Diagnostic Assessment:**  
  If the correct area is imaged, Space Triage provides an initial diagnostic assessment and details on image quality, tissue textures, and anatomical landmarks.

- **Guided Transition Assistance:**  
  If the target area is not captured, the system outputs voice instructions guiding the astronaut to adjust the probe’s position and settings to capture the desired anatomical view.

## How It Works

1. **Area Specification:**  
   The astronaut specifies the anatomical area for analysis by speaking a simple command.

2. **Image Capture and Input:**  
   An ultrasound image is captured using the NASA Ultrasound-2 system and is then fed into Space Triage.

3. **Segmentation Analysis:**  
   The segmentation model processes the image to verify whether the specified anatomical area is present.  
   - **If the target area is found:**  
     The system provides a detailed diagnostic assessment.
   - **If the target area is missing:**  
     Voice-guided instructions are generated to help transition the probe to the correct position.

4. **Voice Guidance and Feedback:**  
   The system’s voice agent produces a transcript that can be read aloud, instructing the astronaut on necessary adjustments. This includes:
   - Verification of the current image.
   - Step-by-step movements and probe positioning.
   - Optimization of machine settings (depth, gain, frequency).
   - Final confirmation when the correct view is achieved.

## Getting Started


## Example Workflow

1. **Astronaut Command:** "Analyze the heart."
2. **Image Capture:** An ultrasound image is taken and fed into the segmentation model.
3. **Segmentation Outcome:**
   - **If the Heart is Visible:**  
     The system says:  
     "The heart is visible. The image displays clear cardiac landmarks including chamber walls and valve motion. Proceed with the cardiac evaluation."
   - **If the Heart is Not Visible:**  
     The system says:  
     "The current image does not show the heart. Please slide the probe upward and adjust the angle slightly toward the chest. Once repositioned, recapture the image."
