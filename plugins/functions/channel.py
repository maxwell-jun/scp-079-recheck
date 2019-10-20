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
from json import dumps
from typing import List, Optional, Union

from pyrogram import Chat, Client, Message
from pyrogram.errors import FloodWait

from .. import glovar
from .etc import code, code_block, general_link, get_forward_name, get_full_name, get_md5sum, get_text, lang
from .etc import message_link, thread, wait_flood
from .file import crypt_file, data_to_file, delete_file, get_new_path, save
from .image import get_file_id
from .telegram import get_group_info, send_document, send_message

# Enable logging
logger = logging.getLogger(__name__)


def ask_for_help(client: Client, level: str, gid: int, uid: int, group: str = "single") -> bool:
    # Let USER help to delete all message from user, or ban user globally
    try:
        data = {
                "group_id": gid,
                "user_id": uid
        }
        should_delete = glovar.configs[gid].get("delete")

        if level == "ban":
            data["type"] = (glovar.configs[gid].get("restrict") and "restrict") or "ban"
            data["delete"] = should_delete
        elif level == "delete":
            data["type"] = group
            if not should_delete:
                return True

        share_data(
            client=client,
            receivers=["USER"],
            action="help",
            action_type=level,
            data=data
        )

        return True
    except Exception as e:
        logger.warning(f"Ask for help error: {e}", exc_info=True)

    return False


def declare_message(client: Client, gid: int, mid: int) -> bool:
    # Declare a message
    try:
        glovar.declared_message_ids[gid].add(mid)
        share_data(
            client=client,
            receivers=glovar.receivers["declare"],
            action="update",
            action_type="declare",
            data={
                "group_id": gid,
                "message_id": mid
            }
        )

        return True
    except Exception as e:
        logger.warning(f"Declare message error: {e}", exc_info=True)

    return False


def exchange_to_hide(client: Client) -> bool:
    # Let other bots exchange data in the hide channel instead
    try:
        glovar.should_hide = True
        share_data(
            client=client,
            receivers=["EMERGENCY"],
            action="backup",
            action_type="hide",
            data=True
        )

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{code(glovar.sender)}\n"
                f"{lang('issue')}{lang('colon')}{code(lang('exchange_invalid'))}\n"
                f"{lang('auto_fix')}{lang('colon')}{code(lang('protocol_1'))}\n")
        thread(send_message, (client, glovar.critical_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Exchange to hide error: {e}", exc_info=True)

    return False


def format_data(sender: str, receivers: List[str], action: str, action_type: str,
                data: Union[bool, dict, int, str] = None) -> str:
    # See https://scp-079.org/exchange/
    text = ""
    try:
        data = {
            "from": sender,
            "to": receivers,
            "action": action,
            "type": action_type,
            "data": data
        }
        text = code_block(dumps(data, indent=4))
    except Exception as e:
        logger.warning(f"Format data error: {e}", exc_info=True)

    return text


def forward_evidence(client: Client, message: Message, level: str, rule: str, score: float = 0.0,
                     more: str = None) -> Optional[Union[bool, Message]]:
    # Forward the message to the logging channel as evidence
    result = None
    try:
        uid = message.from_user.id
        text = (f"{lang('project')}{lang('colon')}{code(glovar.sender)}\n"
                f"{lang('user_id')}{lang('colon')}{code(uid)}\n"
                f"{lang('level')}{lang('colon')}{code(level)}\n"
                f"{lang('rule')}{lang('colon')}{code(rule)}\n")

        if message.game:
            text += f"{lang('message_type')}{lang('colon')}{code(lang('gam'))}\n"
        elif message.service:
            text += f"{lang('message_type')}{lang('colon')}{code(lang('ser'))}\n"

        if message.game:
            text += f"{lang('message_game')}{lang('colon')}{code(message.game.short_name)}\n"

        if lang("score") in rule:
            text += f"{lang('user_score')}{lang('colon')}{code(f'{score:.1f}')}\n"

        if lang("name") in rule:
            name = get_full_name(message.from_user)
            if name:
                text += f"{lang('user_name')}{lang('colon')}{code(name)}\n"

            forward_name = get_forward_name(message)
            if forward_name and forward_name != name:
                text += f"{lang('from_name')}{lang('colon')}{code(forward_name)}\n"

        if message.contact or message.location or message.venue or message.video_note or message.voice:
            text += f"{lang('more')}{lang('colon')}{code(lang('privacy'))}\n"
        elif message.game or message.service:
            text += f"{lang('more')}{lang('colon')}{code(lang('cannot_forward'))}\n"
        elif more:
            text += f"{lang('more')}{lang('colon')}{code(more)}\n"

        # DO NOT try to forward these types of message
        if (message.contact
                or message.location
                or message.venue
                or message.video_note
                or message.voice
                or message.game
                or message.service):
            result = send_message(client, glovar.logging_channel_id, text)
            return result

        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = message.forward(
                    chat_id=glovar.logging_channel_id,
                    disable_notification=True
                )
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
            except Exception as e:
                logger.info(f"Forward evidence message error: {e}", exc_info=True)
                return False

        result = result.message_id
        result = send_message(client, glovar.logging_channel_id, text, result)
    except Exception as e:
        logger.warning(f"Forward evidence error: {e}", exc_info=True)

    return result


def get_content(message: Message) -> str:
    # Get the message that will be added to lists, return the file_id or text's hash
    result = ""
    try:
        if not message:
            return ""

        file_id, _, _ = get_file_id(message)
        text = get_text(message)

        if file_id:
            result += file_id
        elif text:
            result += get_md5sum("string", text)
    except Exception as e:
        logger.warning(f"Get content error: {e}", exc_info=True)

    return result


def get_debug_text(client: Client, context: Union[int, Chat]) -> str:
    # Get a debug message text prefix, accept int or Chat
    text = ""
    try:
        if isinstance(context, int):
            group_id = context
        else:
            group_id = context.id

        group_name, group_link = get_group_info(client, context)
        text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                f"{lang('group_name')}{lang('colon')}{general_link(group_name, group_link)}\n"
                f"{lang('group_id')}{lang('colon')}{code(group_id)}\n")
    except Exception as e:
        logger.warning(f"Get debug text error: {e}", exc_info=True)

    return text


def send_debug(client: Client, chat: Chat, action: str, uid: int, mid: int, em: Message) -> bool:
    # Send the debug message
    try:
        text = get_debug_text(client, chat)
        text += (f"{lang('user_id')}{lang('colon')}{code(uid)}\n"
                 f"{lang('action')}{lang('colon')}{code(action)}\n"
                 f"{lang('triggered_by')}{lang('colon')}{general_link(mid, message_link(em))}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Send debug error: {e}", exc_info=True)

    return False


def share_bad_user(client: Client, uid: int) -> bool:
    # Share a bad user with other bots
    try:
        share_data(
            client=client,
            receivers=glovar.receivers["bad"],
            action="add",
            action_type="bad",
            data={
                "id": uid,
                "type": "user"
            }
        )

        return True
    except Exception as e:
        logger.warning(f"Share bad user error: {e}", exc_info=True)

    return False


def share_data(client: Client, receivers: List[str], action: str, action_type: str,
               data: Union[bool, dict, int, str] = None, file: str = None, encrypt: bool = True) -> bool:
    # Use this function to share data in the channel
    try:
        if glovar.sender in receivers:
            receivers.remove(glovar.sender)

        if not receivers:
            return True

        if glovar.should_hide:
            channel_id = glovar.hide_channel_id
        else:
            channel_id = glovar.exchange_channel_id

        if file:
            text = format_data(
                sender=glovar.sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )
            if encrypt:
                # Encrypt the file, save to the tmp directory
                file_path = get_new_path()
                crypt_file("encrypt", file, file_path)
            else:
                # Send directly
                file_path = file

            result = send_document(client, channel_id, file_path, None, text)
            # Delete the tmp file
            if result:
                for f in {file, file_path}:
                    if "tmp/" in f:
                        thread(delete_file, (f,))
        else:
            text = format_data(
                sender=glovar.sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )
            result = send_message(client, channel_id, text)

        # Sending failed due to channel issue
        if result is False and not glovar.should_hide:
            # Use hide channel instead
            exchange_to_hide(client)
            thread(share_data, (client, receivers, action, action_type, data, file, encrypt))

        return True
    except Exception as e:
        logger.warning(f"Share data error: {e}", exc_info=True)

    return False


def share_regex_count(client: Client, word_type: str) -> bool:
    # Use this function to share regex count to REGEX
    try:
        if not glovar.regex.get(word_type):
            return True

        if not eval(f"glovar.{word_type}_words"):
            return True

        file = data_to_file(eval(f"glovar.{word_type}_words"))
        share_data(
            client=client,
            receivers=["REGEX"],
            action="regex",
            action_type="count",
            data=f"{word_type}_words",
            file=file
        )

        return True
    except Exception as e:
        logger.warning(f"Share regex update error: {e}", exc_info=True)

    return False


def share_watch_user(client: Client, the_type: str, uid: int, until: str) -> bool:
    # Share a watch ban user with other bots
    try:
        share_data(
            client=client,
            receivers=glovar.receivers["watch"],
            action="add",
            action_type="watch",
            data={
                "id": uid,
                "type": the_type,
                "until": until
            }
        )

        return True
    except Exception as e:
        logger.warning(f"Share watch user error: {e}", exc_info=True)

    return False


def update_score(client: Client, uid: int) -> bool:
    # Update a user's score, share it
    try:
        count = len(glovar.user_ids[uid]["detected"])
        score = count * 0.6
        glovar.user_ids[uid]["score"][glovar.sender.lower()] = score
        save("user_ids")
        share_data(
            client=client,
            receivers=glovar.receivers["score"],
            action="update",
            action_type="score",
            data={
                "id": uid,
                "score": round(score, 1)
            }
        )

        return True
    except Exception as e:
        logger.warning(f"Update score error: {e}", exc_info=True)

    return False
