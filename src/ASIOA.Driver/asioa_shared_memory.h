#pragma once

#include <cstdint>

constexpr uint32_t ASIOA_CHANNEL_COUNT = 68;
constexpr uint32_t ASIOA_MAX_BUFFER_SAMPLES = 2048;
constexpr uint32_t ASIOA_SHARED_MEMORY_VERSION = 1;

struct ASIOASharedHeader {
    uint32_t magic;
    uint32_t version;
    uint32_t channelCount;
    uint32_t bufferSamples;
    uint32_t sampleRate;
    uint32_t activeBufferIndex;
    uint64_t driverHeartbeat;
    uint64_t engineHeartbeat;
    uint32_t engineConnected;
    uint32_t safeSilence;
};

constexpr uint32_t ASIOA_MAGIC = 0x414F4953; // SIOA, little endian marker.

struct ASIOASharedAudio {
    ASIOASharedHeader header;
    float hostToEngine[2][ASIOA_CHANNEL_COUNT][ASIOA_MAX_BUFFER_SAMPLES];
    float engineToHost[2][ASIOA_CHANNEL_COUNT][ASIOA_MAX_BUFFER_SAMPLES];
};
