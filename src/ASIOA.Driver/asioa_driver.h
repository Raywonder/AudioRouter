#pragma once

#include "asioa_asio_compat.h"
#include "asioa_shared_memory.h"

#include <cstdint>

// {4B6B66F3-0182-4E8B-9B7C-0C545022110A}
static constexpr GUID CLSID_ASIOA_DRIVER =
    {0x4b6b66f3, 0x0182, 0x4e8b, {0x9b, 0x7c, 0x0c, 0x54, 0x50, 0x22, 0x11, 0x0a}};

class ASIOADriver final : public IASIO {
public:
    ASIOADriver();
    ~ASIOADriver();

    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID riid, void** ppvObject) override;
    ULONG STDMETHODCALLTYPE AddRef() override;
    ULONG STDMETHODCALLTYPE Release() override;

    ASIOBool init(void* sysHandle) override;
    void getDriverName(char* name) override;
    long getDriverVersion() override;
    void getErrorMessage(char* string) override;
    ASIOError start() override;
    ASIOError stop() override;
    ASIOError getChannels(long* numInputChannels, long* numOutputChannels) override;
    ASIOError getLatencies(long* inputLatency, long* outputLatency) override;
    ASIOError getBufferSize(long* minSize, long* maxSize, long* preferredSize, long* granularity) override;
    ASIOError canSampleRate(ASIOSampleRate sampleRate) override;
    ASIOError getSampleRate(ASIOSampleRate* sampleRate) override;
    ASIOError setSampleRate(ASIOSampleRate sampleRate) override;
    ASIOError getClockSources(ASIOClockSource* clocks, long* numSources) override;
    ASIOError setClockSource(long reference) override;
    ASIOError getSamplePosition(ASIOSamples* sPos, ASIOTimeStamp* tStamp) override;
    ASIOError getChannelInfo(ASIOChannelInfo* info) override;
    ASIOError createBuffers(ASIOBufferInfo* bufferInfos, long numChannels, long bufferSize, ASIOCallbacks* callbacks) override;
    ASIOError disposeBuffers() override;
    ASIOError controlPanel() override;
    ASIOError future(long selector, void* opt) override;
    ASIOError outputReady() override;

private:
    volatile long refCount_;
    ASIOSampleRate sampleRate_;
    long bufferSize_;
    bool initialized_;
    bool running_;
    ASIOCallbacks callbacks_;
    ASIOBufferInfo buffers_[ASIOA_CHANNEL_COUNT * 2];
    long bufferCount_;
    char inputNames_[ASIOA_CHANNEL_COUNT][32];
    char outputNames_[ASIOA_CHANNEL_COUNT][32];
    ASIOSamples samplePosition_;
    char lastError_[128];

    void buildChannelNames();
    void setError(const char* text);
    bool supportedSampleRate(ASIOSampleRate sampleRate) const;
    void clearHostBuffers();
};

class ASIOAClassFactory final : public IClassFactory {
public:
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID riid, void** ppvObject) override;
    ULONG STDMETHODCALLTYPE AddRef() override;
    ULONG STDMETHODCALLTYPE Release() override;
    HRESULT STDMETHODCALLTYPE CreateInstance(IUnknown* pUnkOuter, REFIID riid, void** ppvObject) override;
    HRESULT STDMETHODCALLTYPE LockServer(BOOL fLock) override;

private:
    volatile long refCount_{1};
};
