#pragma once

enum class ErrorCode
{
    OK                     = 0x01,
    FILE_META_OPEN_ERROR   = 0x02,
    FILE_META_FORMAT_ERROR = 0x03,
    FILE_META_DATA_ERROR   = 0x04,
    MD5_CHECK_ERROR        = 0x05,
    GAME_FILE_OPEN_ERROR   = 0x06,
    PATCH_FILE_OPEN_ERROR  = 0x07,
};
