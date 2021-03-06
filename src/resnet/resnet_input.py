import os
import tensorflow as tf


def num_examples_per_epoch(subset='train'):
    if subset == 'train':
      return 45000
    elif subset == 'validation':
      return 5000
    elif subset == 'eval':
      return 10000
    else:
      raise ValueError('Invalid data subset "%s"' % subset)


class ResnetInput(object):
  """ resnet 输入 """

  def __init__(self, image_width, image_height, image_depth, data_dir, num_classes, subset='train', use_distortion=True):
    #数据目录
    self.data_dir = data_dir
    #数据级
    self.subset = subset
    #数据变形（预处理）
    self.use_distortion = use_distortion
    #图像宽
    self.WIDTH = image_width
    #图像高
    self.HEIGHT = image_height
    #图像通道数
    self.DEPTH = image_depth
    #分类个数，用于one_hot编码
    self.num_classes = num_classes

  def get_filenames(self):
    if self.subset in ['train', 'validation', 'eval']:
      return [os.path.join(self.data_dir, self.subset + '.tfrecords')]

  def preprocess(self, image):
    if self.subset == "train" and self.use_distortion:
      #图像处理
      image = tf.image.resize_image_with_crop_or_pad(image, self.WIDTH, self.HEIGHT)
      #反转图片，如果输入样本长宽不一致，则无法反转
      image = tf.random_crop(image, [self.HEIGHT, self.WIDTH, self.DEPTH])
      image = tf.image.random_flip_left_right(image)
    return image

  def parser(self, serialized_example):
    features = tf.parse_single_example(
        serialized_example,
        features={
            'image': tf.FixedLenFeature([], tf.string),
            'label': tf.FixedLenFeature([], tf.int64),
        })
    image = tf.decode_raw(features['image'], tf.uint8)
    image.set_shape([self.DEPTH * self.HEIGHT * self.WIDTH])
    image = tf.cast(tf.transpose(tf.reshape(image, [self.DEPTH, self.HEIGHT, self.WIDTH]), [1, 2, 0]), tf.float32)
    label = tf.cast(features['label'], tf.int32)
    #不使用one_hot转码
    label = tf.one_hot(label,depth = self.num_classes)
    #preprocess
    #image = self.preprocess(image)
    return image, label

  # batch_size -> 批尺寸，即学习一次使用的数据集中数据个数
  def make_batch(self, batch_size):
    filenames = self.get_filenames()
    #读取dataset
    dataset = tf.data.TFRecordDataset(filenames).repeat()
    #循环读取
    dataset = dataset.map(self.parser)
    #处理train样本集
    if self.subset == 'train':
      #预计数量*0.4构建随机乱序batch
      min_queue_examples = int(num_examples_per_epoch(self.subset)*0.4)
      #确保整体容量能够生成较为优质的batch
      dataset = dataset.shuffle(buffer_size=min_queue_examples + 3 * batch_size)
    #打包
    dataset = dataset.batch(batch_size)
    #构建迭代tesnor
    iterator = dataset.make_one_shot_iterator()
    #获取图片tensor和标注tensor
    image_batch, label_batch = iterator.get_next(name="input")
    #返回tensor
    return image_batch, label_batch

#example
if __name__ == '__main__':
  train = 'debug/resnet/'
  input = ResnetInput(data_dir=train, image_width = 10, image_height =10, image_depth=1,num_classes = 11)
  image_bacth,label_bacth =  input.make_batch(11)
  #使用session测试读取结果
  with tf.Session() as sess:
    #print(run_image_bacth)
    print(sess.run(image_bacth))
    print(sess.run(label_bacth))
