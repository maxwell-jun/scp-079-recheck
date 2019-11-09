# SCP-079-RECHECK - Recheck NSFW media messages
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-RECHECK.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import re

from pyrogram import Client, Message

from .. import glovar
from .channel import get_content
from .etc import code, get_int, get_md5sum, get_text, lang, mention_id, thread
from .file import delete_file, get_downloaded_path
from .filters import is_detected_url
from .image import get_file_id, get_porn_a, get_porn_b
from .telegram import send_message

# Enable logging
logger = logging.getLogger(__name__)


def porn_test(client: Client, message: Message) -> bool:
    # Test image porn score in the test group
    try:
        origin_text = get_text(message)
        if re.search(f"^{lang('admin')}{lang('colon')}[0-9]", origin_text):
            aid = get_int(origin_text.split("\n\n")[0].split(lang('colon'))[1])
        else:
            aid = message.from_user.id

        text = ""

        # Detected record
        content = get_content(message)
        detection = glovar.contents.get(content, "")
        if detection == "nsfw":
            text += f"{lang('record_content')}{lang('colon')}{code('True')}\n"

        # Detected url
        detection = is_detected_url(message)
        if detection:
            text += f"{lang('record_link')}{lang('colon')}{code(code('True'))}\n"

        # Get the image
        file_id, file_ref, _ = get_file_id(message)
        image_path = get_downloaded_path(client, file_id, file_ref)
        image_hash = image_path and get_md5sum("file", image_path)

        # Send the result
        whitelisted = ((content and (content in glovar.except_ids["long"] or content in glovar.except_ids["temp"]))
                       or image_hash in glovar.except_ids["temp"])
        text += f"{lang('white_listed')}{lang('colon')}{code(whitelisted)}\n"
        text = f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n\n" + text
        thread(send_message, (client, glovar.test_group_id, text, message.message_id))

        # Model A
        porn_a = image_path and get_porn_a(image_path)
        if porn_a:
            text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n\n"
                    f"{lang('model_recheck')}{lang('colon')}{code('A')}\n")

            for image_type in ["drawings", "hentai", "neutral", "porn", "sexy"]:
                text += f"{lang(image_type)}{lang('colon')}{code(f'{porn_a[image_type]:.8f}')}\n"

            thread(send_message, (client, glovar.test_group_id, text, message.message_id))

        # Model B
        porn_b = get_porn_b(image_path)
        if porn_b:
            text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n\n"
                    f"{lang('model_recheck')}{lang('colon')}{code('B')}\n")

            for image_type in ["drawings", "hentai", "neutral", "porn", "sexy"]:
                text += f"{lang(image_type)}{lang('colon')}{code(f'{porn_b[image_type]:.8f}')}\n"

            thread(send_message, (client, glovar.test_group_id, text, message.message_id))

        # Delete the image file
        image_path and delete_file(image_path)

        return True
    except Exception as e:
        logger.warning(f"Porn test error: {e}", exc_info=True)

    return False
