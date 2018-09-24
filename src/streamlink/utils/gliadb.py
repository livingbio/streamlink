import os
import re
import logging
import tempfile

from django.core.files.base import File

import gffmpeg

from video.models import Clip, Image

log = logging.getLogger(__name__)

re_offset = re.compile(r', start: (?P<offset>[\d\.]+),')


def save(sequence, result, video_obj):
    video = video_obj

    ts_idx = sequence.num
    duration = sequence.segment.duration

    ts_filepath = '{}/{}-{}.ts'.format(video.cache_dir, duration, ts_idx)
    ts_name = '{}-{}.ts'.format(duration, ts_idx)
    with open(ts_filepath, 'wb') as f:
        f.write(result.content)

    offset = get_offset(ts_filepath)
    if not offset:  # skip if no offset detect.
        return

    # save clips
    try:
        clip, _ = Clip.objects.update_or_create(video=video, offset=offset, sequence=ts_idx,
                                                defaults={'duration': duration})
        with open(ts_filepath, 'rb') as ts_file:
            clip.file.save(ts_name, File(ts_file))

        log.debug('save clip sequence: {0}', ts_idx)

    except Exception as e:
        log.error('error happened when store clip sequence: {0}', ts_idx)
        log.error('exception:')
        log.error(e)

    # save thumbnail
    screenshots = gffmpeg.sample_images(ts_filepath, 1, fast=False)
    for idx, image_path in enumerate(screenshots):
        image_name = os.path.basename(image_path)

        try:
            image, _ = Image.objects.update_or_create(
                video=video,
                offset=offset + idx
            )
            with open(image_path, 'rb') as image_file:
                image.file.save(image_name, File(image_file))

        except Exception as e:
            log.error('error happened when store image in sequence: {0}', ts_idx)
            log.error('exception:')
            log.error(e)

        os.remove(image_path)  # cleanup

    os.remove(ts_filepath)  # cleanup


def get_offset(filepath):
    message = gffmpeg.execute(['ffmpeg', '-i', filepath], ignore_error=True)
    match = re.search(re_offset, message)
    if not match:
        return None

    offset = match.group('offset')
    return float(offset)
