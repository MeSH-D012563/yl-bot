import os
import replicate
from dotenv import load_dotenv
import requests
from PIL import Image
import io

# Load environment variables
load_dotenv()

class VirtualTryOn:
    def __init__(self):
        self.api_token = os.getenv('REPLICATE_API_TOKEN')
        if not self.api_token:
            raise ValueError("REPLICATE_API_TOKEN environment variable is not set")
        
        # Set the API token for replicate
        os.environ["REPLICATE_API_TOKEN"] = self.api_token

    def try_on(self, garment_image_path, human_image_path, garment_description):
        """
        Perform virtual try-on using IDM-VTON model
        
        Args:
            garment_image_path (str): Path to the garment image
            human_image_path (str): Path to the human image
            garment_description (str): Description of the garment
            
        Returns:
            bytes: The resulting image data
        """
        try:
            # Read the images
            with open(garment_image_path, 'rb') as f:
                garment_img = f.read()
            
            with open(human_image_path, 'rb') as f:
                human_img = f.read()

            # Prepare input for the model
            input_data = {
                "garm_img": garment_img,
                "human_img": human_img,
                "garment_des": garment_description
            }

            # Run the model
            output = replicate.run(
                "cuuupid/idm-vton:0513734a452173b8173e907e3a59d19a36266e55b48528559432bd21c7d7e985",
                input=input_data
            )

            # Save the output image
            output_path = "tryon_result.jpg"
            with open(output_path, "wb") as file:
                file.write(output.read())
            
            return output_path

        except Exception as e:
            print(f"Error during virtual try-on: {str(e)}")
            return None

    def save_image_from_url(self, url, save_path):
        """
        Download and save an image from URL
        
        Args:
            url (str): URL of the image
            save_path (str): Path where to save the image
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            print(f"Error downloading image: {str(e)}")
            return False 