#include "asioa_driver.h"

#include <shellapi.h>
#include <stdio.h>
#include <strsafe.h>
#include <string.h>

namespace {
volatile long g_lockCount = 0;
volatile long g_objectCount = 0;

void copyText(char* dest, size_t size, const char* source) {
    if (!dest || size == 0) {
        return;
    }
    strncpy_s(dest, size, source ? source : "", _TRUNCATE);
}

}

ASIOADriver::ASIOADriver()
    : refCount_(1),
      sampleRate_(48000.0),
      bufferSize_(128),
      initialized_(false),
      running_(false),
      callbacks_{},
      buffers_{},
      bufferCount_(0),
      samplePosition_{0, 0},
      lastError_{} {
    buildChannelNames();
    copyText(lastError_, sizeof(lastError_), "No error.");
    InterlockedIncrement(&g_objectCount);
}

ASIOADriver::~ASIOADriver() {
    disposeBuffers();
    InterlockedDecrement(&g_objectCount);
}

HRESULT STDMETHODCALLTYPE ASIOADriver::QueryInterface(REFIID riid, void** ppvObject) {
    if (!ppvObject) {
        return E_POINTER;
    }
    if (riid == IID_IUnknown || riid == CLSID_ASIOA_DRIVER) {
        *ppvObject = static_cast<IASIO*>(this);
        AddRef();
        return S_OK;
    }
    *ppvObject = nullptr;
    return E_NOINTERFACE;
}

ULONG STDMETHODCALLTYPE ASIOADriver::AddRef() {
    return static_cast<ULONG>(InterlockedIncrement(&refCount_));
}

ULONG STDMETHODCALLTYPE ASIOADriver::Release() {
    ULONG count = static_cast<ULONG>(InterlockedDecrement(&refCount_));
    if (count == 0) {
        delete this;
    }
    return count;
}

ASIOBool ASIOADriver::init(void*) {
    initialized_ = true;
    return 1;
}

void ASIOADriver::getDriverName(char* name) {
    copyText(name, 32, "ASIOA Audio Router");
}

long ASIOADriver::getDriverVersion() {
    return 203;
}

void ASIOADriver::getErrorMessage(char* string) {
    copyText(string, 128, lastError_);
}

ASIOError ASIOADriver::start() {
    if (!initialized_) {
        setError("Driver has not been initialized.");
        return ASE_InvalidMode;
    }
    running_ = true;
    clearHostBuffers();
    return ASE_OK;
}

ASIOError ASIOADriver::stop() {
    running_ = false;
    return ASE_OK;
}

ASIOError ASIOADriver::getChannels(long* numInputChannels, long* numOutputChannels) {
    if (!numInputChannels || !numOutputChannels) {
        return ASE_InvalidParameter;
    }
    *numInputChannels = ASIOA_CHANNEL_COUNT;
    *numOutputChannels = ASIOA_CHANNEL_COUNT;
    return ASE_OK;
}

ASIOError ASIOADriver::getLatencies(long* inputLatency, long* outputLatency) {
    if (!inputLatency || !outputLatency) {
        return ASE_InvalidParameter;
    }
    *inputLatency = bufferSize_;
    *outputLatency = bufferSize_;
    return ASE_OK;
}

ASIOError ASIOADriver::getBufferSize(long* minSize, long* maxSize, long* preferredSize, long* granularity) {
    if (!minSize || !maxSize || !preferredSize || !granularity) {
        return ASE_InvalidParameter;
    }
    *minSize = 16;
    *maxSize = ASIOA_MAX_BUFFER_SAMPLES;
    *preferredSize = bufferSize_;
    *granularity = -1;
    return ASE_OK;
}

ASIOError ASIOADriver::canSampleRate(ASIOSampleRate sampleRate) {
    return supportedSampleRate(sampleRate) ? ASE_OK : ASE_NoClock;
}

ASIOError ASIOADriver::getSampleRate(ASIOSampleRate* sampleRate) {
    if (!sampleRate) {
        return ASE_InvalidParameter;
    }
    *sampleRate = sampleRate_;
    return ASE_OK;
}

ASIOError ASIOADriver::setSampleRate(ASIOSampleRate sampleRate) {
    if (!supportedSampleRate(sampleRate)) {
        setError("Unsupported sample rate.");
        return ASE_NoClock;
    }
    sampleRate_ = sampleRate;
    return ASE_OK;
}

ASIOError ASIOADriver::getClockSources(ASIOClockSource* clocks, long* numSources) {
    if (!numSources) {
        return ASE_InvalidParameter;
    }
    if (!clocks) {
        *numSources = 1;
        return ASE_OK;
    }
    clocks[0] = {};
    clocks[0].index = 0;
    clocks[0].isCurrentSource = 1;
    copyText(clocks[0].name, sizeof(clocks[0].name), "ASIOA software clock");
    *numSources = 1;
    return ASE_OK;
}

ASIOError ASIOADriver::setClockSource(long reference) {
    if (reference != 0) {
        return ASE_InvalidParameter;
    }
    return ASE_OK;
}

ASIOError ASIOADriver::getSamplePosition(ASIOSamples* sPos, ASIOTimeStamp* tStamp) {
    if (!sPos || !tStamp) {
        return ASE_InvalidParameter;
    }
    *sPos = samplePosition_;
    ULONGLONG now = GetTickCount64();
    tStamp->hi = static_cast<unsigned long>((now >> 32) & 0xffffffffu);
    tStamp->lo = static_cast<unsigned long>(now & 0xffffffffu);
    return ASE_OK;
}

ASIOError ASIOADriver::getChannelInfo(ASIOChannelInfo* info) {
    if (!info || info->channel < 0 || info->channel >= static_cast<long>(ASIOA_CHANNEL_COUNT)) {
        return ASE_InvalidParameter;
    }
    info->isActive = 1;
    info->channelGroup = info->channel / 2;
    info->type = ASIOSTFloat32LSB;
    const char* name = info->isInput ? inputNames_[info->channel] : outputNames_[info->channel];
    copyText(info->name, sizeof(info->name), name);
    return ASE_OK;
}

ASIOError ASIOADriver::createBuffers(ASIOBufferInfo* bufferInfos, long numChannels, long bufferSize, ASIOCallbacks* callbacks) {
    if (!bufferInfos || !callbacks || numChannels <= 0 || bufferSize < 16 || bufferSize > static_cast<long>(ASIOA_MAX_BUFFER_SAMPLES)) {
        return ASE_InvalidParameter;
    }
    callbacks_ = *callbacks;
    bufferSize_ = bufferSize;
    long boundedCount = numChannels > static_cast<long>(ASIOA_CHANNEL_COUNT * 2) ? static_cast<long>(ASIOA_CHANNEL_COUNT * 2) : numChannels;
    for (long index = 0; index < boundedCount; ++index) {
        buffers_[index] = bufferInfos[index];
    }
    bufferCount_ = boundedCount;
    clearHostBuffers();
    return ASE_OK;
}

ASIOError ASIOADriver::disposeBuffers() {
    bufferCount_ = 0;
    callbacks_ = {};
    return ASE_OK;
}

ASIOError ASIOADriver::controlPanel() {
    wchar_t path[MAX_PATH]{};
    DWORD length = GetEnvironmentVariableW(L"ProgramFiles", path, MAX_PATH);
    wchar_t exe[MAX_PATH]{};
    if (length > 0) {
        StringCchPrintfW(exe, MAX_PATH, L"%s\\ASIOA Audio Router\\ASIOA Audio Router.exe", path);
    } else {
        StringCchCopyW(exe, MAX_PATH, L"C:\\Program Files\\ASIOA Audio Router\\ASIOA Audio Router.exe");
    }
    ShellExecuteW(nullptr, L"open", exe, nullptr, nullptr, SW_SHOWNORMAL);
    return ASE_OK;
}

ASIOError ASIOADriver::future(long, void*) {
    return ASE_NotPresent;
}

ASIOError ASIOADriver::outputReady() {
    return ASE_OK;
}

void ASIOADriver::buildChannelNames() {
    for (uint32_t channel = 0; channel < ASIOA_CHANNEL_COUNT; ++channel) {
        char inputName[32]{};
        char outputName[32]{};
        sprintf_s(inputName, sizeof(inputName), "ASIOA In %u", channel + 1);
        sprintf_s(outputName, sizeof(outputName), "ASIOA Out %u", channel + 1);
        copyText(inputNames_[channel], sizeof(inputNames_[channel]), inputName);
        copyText(outputNames_[channel], sizeof(outputNames_[channel]), outputName);
    }
    copyText(outputNames_[0], sizeof(outputNames_[0]), "Main Out L");
    copyText(outputNames_[1], sizeof(outputNames_[1]), "Main Out R");
    copyText(inputNames_[60], sizeof(inputNames_[60]), "Screen Reader L");
    copyText(inputNames_[61], sizeof(inputNames_[61]), "Screen Reader R");
    copyText(inputNames_[62], sizeof(inputNames_[62]), "TTS L");
    copyText(inputNames_[63], sizeof(inputNames_[63]), "TTS R");
    copyText(inputNames_[64], sizeof(inputNames_[64]), "Communications L");
    copyText(inputNames_[65], sizeof(inputNames_[65]), "Communications R");
    copyText(inputNames_[66], sizeof(inputNames_[66]), "Emergency L");
    copyText(inputNames_[67], sizeof(inputNames_[67]), "Emergency R");
}

void ASIOADriver::setError(const char* text) {
    copyText(lastError_, sizeof(lastError_), text);
}

bool ASIOADriver::supportedSampleRate(ASIOSampleRate sampleRate) const {
    return sampleRate == 44100.0 || sampleRate == 48000.0 || sampleRate == 88200.0 ||
           sampleRate == 96000.0 || sampleRate == 176400.0 || sampleRate == 192000.0;
}

void ASIOADriver::clearHostBuffers() {
    for (long index = 0; index < bufferCount_; ++index) {
        for (void* raw : buffers_[index].buffers) {
            if (raw) {
                memset(raw, 0, static_cast<size_t>(bufferSize_) * sizeof(float));
            }
        }
    }
}

HRESULT STDMETHODCALLTYPE ASIOAClassFactory::QueryInterface(REFIID riid, void** ppvObject) {
    if (!ppvObject) {
        return E_POINTER;
    }
    if (riid == IID_IUnknown || riid == IID_IClassFactory) {
        *ppvObject = static_cast<IClassFactory*>(this);
        AddRef();
        return S_OK;
    }
    *ppvObject = nullptr;
    return E_NOINTERFACE;
}

ULONG STDMETHODCALLTYPE ASIOAClassFactory::AddRef() {
    return static_cast<ULONG>(InterlockedIncrement(&refCount_));
}

ULONG STDMETHODCALLTYPE ASIOAClassFactory::Release() {
    ULONG count = static_cast<ULONG>(InterlockedDecrement(&refCount_));
    if (count == 0) {
        delete this;
    }
    return count;
}

HRESULT STDMETHODCALLTYPE ASIOAClassFactory::CreateInstance(IUnknown* pUnkOuter, REFIID riid, void** ppvObject) {
    if (pUnkOuter) {
        return CLASS_E_NOAGGREGATION;
    }
    auto* driver = new ASIOADriver();
    if (!driver) {
        return E_OUTOFMEMORY;
    }
    HRESULT hr = driver->QueryInterface(riid, ppvObject);
    driver->Release();
    return hr;
}

HRESULT STDMETHODCALLTYPE ASIOAClassFactory::LockServer(BOOL fLock) {
    if (fLock) {
        InterlockedIncrement(&g_lockCount);
    } else {
        InterlockedDecrement(&g_lockCount);
    }
    return S_OK;
}

extern "C" HRESULT __stdcall DllCanUnloadNow() {
    return (g_objectCount == 0 && g_lockCount == 0) ? S_OK : S_FALSE;
}

extern "C" HRESULT __stdcall DllGetClassObject(REFCLSID rclsid, REFIID riid, void** ppv) {
    if (rclsid != CLSID_ASIOA_DRIVER) {
        return CLASS_E_CLASSNOTAVAILABLE;
    }
    auto* factory = new ASIOAClassFactory();
    HRESULT hr = factory->QueryInterface(riid, ppv);
    factory->Release();
    return hr;
}
