# Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""CARLA sensors."""


import os

from collections import namedtuple

try:
    import numpy
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed.')

from .transform import Transform, Translation, Rotation, Scale


# ==============================================================================
# -- Helpers -------------------------------------------------------------------
# ==============================================================================


Color = namedtuple('Color', 'r g b')
Color.__new__.__defaults__ = (0, 0, 0)


Point = namedtuple('Point', 'x y z color')
Point.__new__.__defaults__ = (0.0, 0.0, 0.0, None)


def _append_extension(filename, ext):
    return filename if filename.lower().endswith(ext.lower()) else filename + ext


# ==============================================================================
# -- Sensor --------------------------------------------------------------------
# ==============================================================================


class Sensor(object):
    """
    Base class for sensor descriptions. Used to add sensors to CarlaSettings.
    """

    def __init__(self, name, sensor_type):
        self.SensorName = name
        self.SensorType = sensor_type
        self.PositionX = 0.2
        self.PositionY = 0.0
        self.PositionZ = 1.3
        self.RotationPitch = 0.0
        self.RotationRoll = 0.0
        self.RotationYaw = 0.0
        self.GaussianNoise = 0.0  # claude
        self.DropOutPattern = 1.0  # claude
        self.LidarType = 1  # claude
        self.DebugFlag = 0
        self.HorizonRange = 360.0
    def set(self, **kwargs):
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise ValueError('sensor.Sensor: no key named %r' % key)
            setattr(self, key, value)

    def set_position(self, x, y, z):
        self.PositionX = x
        self.PositionY = y
        self.PositionZ = z

    def set_rotation(self, pitch, yaw, roll):
        self.RotationPitch = pitch
        self.RotationYaw = yaw
        self.RotationRoll = roll

    def get_transform(self):
        '''
        Returns the camera to [whatever the camera is attached to]
        transformation.
        '''
        return Transform(
            Translation(self.PositionX, self.PositionY, self.PositionZ),
            Rotation(self.RotationPitch, self.RotationYaw, self.RotationRoll))

    def get_unreal_transform(self):
        '''
        Returns the camera to [whatever the camera is attached to]
        transformation with the Unreal necessary corrections applied.

        @todo Do we need to expose this?
        '''
        to_unreal_transform = Transform(Rotation(roll=-90, yaw=90), Scale(x=-1))
        return self.get_transform() * to_unreal_transform


class Camera(Sensor):
    """
    Camera description. This class can be added to a CarlaSettings object to add
    a camera to the player vehicle.
    """

    def __init__(self, name, **kwargs):
        super(Camera, self).__init__(name, sensor_type="CAMERA")
        self.PostProcessing = 'SceneFinal'
        self.ImageSizeX = 720
        self.ImageSizeY = 512
        self.FOV = 90.0
        self.set(**kwargs)

    def set_image_size(self, pixels_x, pixels_y):
        '''Sets the image size in pixels'''
        self.ImageSizeX = pixels_x
        self.ImageSizeY = pixels_y


class Lidar(Sensor):
    """
    Lidar description. This class can be added to a CarlaSettings object to add
    a Lidar to the player vehicle.
    """

    def __init__(self, name, **kwargs):
        super(Lidar, self).__init__(name, sensor_type="LIDAR_RAY_CAST")
        self.Channels = 32
        self.Range = 50.0
        self.PointsPerSecond = 56000
        self.RotationFrequency = 10.0
        self.UpperFovLimit = 10.0
        self.LowerFovLimit = -30.0
        self.ShowDebugPoints = False
        self.set(**kwargs)


# ==============================================================================
# -- SensorData ----------------------------------------------------------------
# ==============================================================================


class SensorData(object):
    """Base class for sensor data returned from the server."""
    def __init__(self, frame_number):
        self.frame_number = frame_number


class Image(SensorData):
    """Data generated by a Camera."""

    def __init__(self, frame_number, width, height, image_type, fov, raw_data):
        super(Image, self).__init__(frame_number=frame_number)
        assert len(raw_data) == 4 * width * height
        self.width = width
        self.height = height
        self.type = image_type
        self.fov = fov
        self.raw_data = raw_data
        self._converted_data = None

    @property
    def data(self):
        """
        Lazy initialization for data property, stores converted data in its
        default format.
        """
        if self._converted_data is None:
            from . import image_converter

            if self.type == 'Depth':
                self._converted_data = image_converter.depth_to_array(self)
            elif self.type == 'SemanticSegmentation':
                self._converted_data = image_converter.labels_to_array(self)
            else:
                self._converted_data = image_converter.to_rgb_array(self)
        return self._converted_data

    def save_to_disk(self, filename):
        """Save this image to disk (requires PIL installed)."""
        filename = _append_extension(filename, '.png')

        try:
            from PIL import Image as PImage
        except ImportError:
            raise RuntimeError(
                'cannot import PIL, make sure pillow package is installed')

        image = PImage.frombytes(
            mode='RGBA',
            size=(self.width, self.height),
            data=self.raw_data,
            decoder_name='raw')
        color = image.split()
        image = PImage.merge("RGB", color[2::-1])

        folder = os.path.dirname(filename)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        image.save(filename)


class PointCloud(SensorData):
    """A list of points."""

    def __init__(self, frame_number, array, color_array=None):
        super(PointCloud, self).__init__(frame_number=frame_number)
        self._array = array
        self._color_array = color_array
        self._has_colors = color_array is not None

    @property
    def array(self):
        """The numpy array holding the point-cloud.

        3D points format for n elements:
        [ [X0,Y0,Z0],
          ...,
          [Xn,Yn,Zn] ]
        """
        return self._array

    @property
    def color_array(self):
        """The numpy array holding the colors corresponding to each point.
        It is None if there are no colors.

        Colors format for n elements:
        [ [R0,G0,B0],
          ...,
          [Rn,Gn,Bn] ]
        """
        return self._color_array

    def has_colors(self):
        """Return whether the points have color."""
        return self._has_colors

    def apply_transform(self, transformation):
        """Modify the PointCloud instance transforming its points"""
        self._array = transformation.transform_points(self._array)

    def save_to_disk(self, filename):
        """Save this point-cloud to disk as PLY format."""
        filename = _append_extension(filename, '.ply')

        def construct_ply_header():
            """Generates a PLY header given a total number of 3D points and
            coloring property if specified
            """
            points = len(self)  # Total point number
            header = ['ply',
                      'format ascii 1.0',
                      'element vertex {}',
                      'property float32 x',
                      'property float32 y',
                      'property float32 z',
                      'property uchar diffuse_red',
                      'property uchar diffuse_green',
                      'property uchar diffuse_blue',
                      'end_header']
            if not self._has_colors:
                return '\n'.join(header[0:6] + [header[-1]]).format(points)
            return '\n'.join(header).format(points)

        if not self._has_colors:
            ply = '\n'.join(['{:.2f} {:.2f} {:.2f}'.format(
                *p) for p in self._array.tolist()])
        else:
            points_3d = numpy.concatenate(
                (self._array, self._color_array), axis=1)
            ply = '\n'.join(['{:.2f} {:.2f} {:.2f} {:.0f} {:.0f} {:.0f}'
                             .format(*p) for p in points_3d.tolist()])

        # Create folder to save if does not exist.
        folder = os.path.dirname(filename)
        if not os.path.isdir(folder):
            os.makedirs(folder)

        # Open the file and save with the specific PLY format.
        with open(filename, 'w+') as ply_file:
            ply_file.write('\n'.join([construct_ply_header(), ply]))

    def __len__(self):
        return len(self.array)

    def __getitem__(self, key):
        color = None if self._color_array is None else Color(
            *self._color_array[key])
        return Point(*self._array[key], color=color)

    def __iter__(self):
        class PointIterator(object):
            """Iterator class for PointCloud"""

            def __init__(self, point_cloud):
                self.point_cloud = point_cloud
                self.index = -1

            def __next__(self):
                self.index += 1
                if self.index >= len(self.point_cloud):
                    raise StopIteration
                return self.point_cloud[self.index]

            def next(self):
                return self.__next__()

        return PointIterator(self)

    def __str__(self):
        return str(self.array)


class LidarMeasurement(SensorData):
    """Data generated by a Lidar."""

    def __init__(self, frame_number, horizontal_angle, channels, point_count_by_channel, point_cloud):
        super(LidarMeasurement, self).__init__(frame_number=frame_number)
        assert numpy.sum(point_count_by_channel) == len(point_cloud.array)
        self.horizontal_angle = horizontal_angle
        self.channels = channels
        self.point_count_by_channel = point_count_by_channel
        self.point_cloud = point_cloud

    @property
    def data(self):
        """The numpy array holding the point-cloud.

        3D points format for n elements:
        [ [X0,Y0,Z0],
          ...,
          [Xn,Yn,Zn] ]
        """
        return self.point_cloud.array

    def save_to_disk(self, filename):
        """Save point-cloud to disk as PLY format."""
        self.point_cloud.save_to_disk(filename)
