import json

import cv2
import numpy as np
from PIL import Image

from invokeai.invocation_api import (
    BaseInvocation,
    BaseInvocationOutput,
    FloatOutput,
    ImageField,
    ImageOutput,
    InputField,
    IntegerOutput,
    InvocationContext,
    OutputField,
    invocation,
    invocation_output,
)


@invocation(
    "load_video_frame",
    title="Load Video Frame",
    tags=["video", "load", "frame"],
    category="image",
    version="1.1.0",
)
class LoadVideoFrameInvocation(BaseInvocation):
    """Load a specific frame from an MP4 video and provide it as output."""

    # Inputs
    video_path: str = InputField(description="The path to the MP4 video file")
    frame_number: int = InputField(default=1, ge=1, description="The frame number to load")

    def invoke(self, context: InvocationContext) -> ImageOutput:
        # Open the video file
        video = cv2.VideoCapture(self.video_path)
        if not video.isOpened():
            # Ensure release even if opening failed partially
            video.release()
            raise ValueError(f"Could not open video file: {self.video_path}")

        # Set the frame position
        video.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number - 1)

        # Read the frame
        ret, frame = video.read()

        # Close the video file
        video.release()

        if not ret:
            raise Exception(f"Failed to read frame {self.frame_number} from video {self.video_path}")

        # Convert the frame to a PIL Image
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # Create the ImageField object
        image_dto = context.images.save(image=image)

        return ImageOutput.build(image_dto)


@invocation_output("image_index_collect_output")
class ImageIndexCollectOutput(BaseInvocationOutput):
    """XImageCollectOutput string containing an array of xItem, Image_name converted to json"""

    image_index_collection: str = OutputField(description="The Image Index Collection ")


@invocation(
    "image_index_collect",
    title="Image Index Collect",
    tags=["video", "collection", "image", "index", "frame"],
    category="collections",
    version="1.1.0",
)
class ImageIndexCollectInvocation(BaseInvocation):
    """ImageIndexCollect takes Image and Index then outputs it as an (index,image_name)array converted to json"""

    index: int = InputField(default=0, description="The index")
    image: ImageField = InputField(default=None, description="The image associated with the index")

    def invoke(self, context: InvocationContext) -> ImageIndexCollectOutput:
        """Invoke with provided services and return outputs."""
        return ImageIndexCollectOutput(image_index_collection=json.dumps([self.index, self.image.image_name]))


@invocation_output("ImagesIndexToVideoOutput")
class ImagesIndexToVideoOutput(BaseInvocationOutput):
    """ImagesIndexToVideoOutput returns nothing"""


@invocation(
    "images_index_to_video",
    title="Images Index To Video Output",
    tags=["video", "collection", "image", "index", "frame"],
    category="collections",
    version="1.1.0",
)
class ImagesIndexToVideoInvocation(BaseInvocation):
    """Load a collection of ImageIndex types (json of (idex,image_name)array) and create a video of them"""

    image_index_collection: list[str] = InputField(description="The Image Index Collection")
    video_out_path: str = InputField(default="", description="Path and filename of output mp4")
    fps: float = InputField(default=30, description="FPS")
    codec: str = InputField(
        min_length=4,
        max_length=4,
        default="x264",
        description="Video codec FourCC (e.g., mp4v, avc1, h264, x264, hev1, vp09, av01)",
    )

    def invoke(self, context: InvocationContext) -> ImagesIndexToVideoOutput:
        """Convert an image list a video"""
        new_array = sorted([json.loads(s) for s in self.image_index_collection], key=lambda x: x[0])
        image = context.images.get_pil(new_array[0][1])

        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        video_writer = cv2.VideoWriter(self.video_out_path, fourcc, self.fps, (image.width, image.height))
        if not video_writer.isOpened():
            raise RuntimeError(f"Failed to open video writer for path {self.video_out_path} with codec {self.codec}")

        for item in new_array:
            image = context.images.get_pil(item[1])
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            video_writer.write(image)

        video_writer.release()

        return ImagesIndexToVideoOutput()


@invocation(
    "get_total_frames",
    title="Get Total Frames",
    tags=["video", "frames", "count"],
    category="video",
    version="1.1.0",
)
class GetTotalFramesInvocation(BaseInvocation):
    """Get the total number of frames in an MP4 video and provide it as output."""

    # Inputs
    video_path: str = InputField(description="The path to the MP4 video file")

    def invoke(self, context: InvocationContext) -> IntegerOutput:
        # Open the video file
        video = cv2.VideoCapture(self.video_path)

        # Get the total number of frames
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

        # Close the video file
        video.release()

        return IntegerOutput(value=total_frames)


@invocation(
    "get_source_framerate",
    title="Get Source Frame Rate",
    tags=["video", "framerate"],
    category="video",
    version="1.1.0",
)
class GetSourceFrameRateInvocation(BaseInvocation):
    """Get the source framerate of an MP4 video and provide it as output."""

    # Inputs
    video_path: str = InputField(description="The path to the MP4 video file")

    def invoke(self, context: InvocationContext) -> FloatOutput:
        # Open the video file
        video = cv2.VideoCapture(self.video_path)

        # Get the source framerate
        framerate = float(video.get(cv2.CAP_PROP_FPS))

        # Close the video file
        video.release()

        return FloatOutput(value=framerate)


@invocation_output("image_to_image_name_output")
class ImageToImageNameOutput(BaseInvocationOutput):
    """Output class for Image to Image Name Invocation"""

    image_name: str = OutputField(description="The name of the image")


@invocation(
    "image_to_image_name",
    title="Image to Image Name",
    tags=["image", "name", "utility"],
    category="utility",
    version="1.1.0",
)
class ImageToImageNameInvocation(BaseInvocation):
    """Invocation to extract the image name from an ImageField."""

    # Input
    image: ImageField = InputField(description="The ImageField to extract the name from")

    def invoke(self, context: InvocationContext) -> ImageToImageNameOutput:
        """Invoke method to extract the image name."""
        # Extract the image name
        image_name = self.image.image_name

        # Return the image name in the output
        return ImageToImageNameOutput(image_name=image_name)
