#include "asioa_driver.h"

#include <strsafe.h>

namespace {
HMODULE g_module = nullptr;

bool modulePath(wchar_t* path, DWORD count) {
    return GetModuleFileNameW(g_module, path, count) > 0;
}

HRESULT setStringValue(HKEY root, const wchar_t* subkey, const wchar_t* name, const wchar_t* value) {
    HKEY key{};
    LSTATUS status = RegCreateKeyExW(root, subkey, 0, nullptr, REG_OPTION_NON_VOLATILE, KEY_WRITE, nullptr, &key, nullptr);
    if (status != ERROR_SUCCESS) {
        return HRESULT_FROM_WIN32(status);
    }
    status = RegSetValueExW(key, name, 0, REG_SZ, reinterpret_cast<const BYTE*>(value), static_cast<DWORD>((wcslen(value) + 1) * sizeof(wchar_t)));
    RegCloseKey(key);
    return HRESULT_FROM_WIN32(status);
}

HRESULT deleteTree(HKEY root, const wchar_t* subkey) {
    LSTATUS status = RegDeleteTreeW(root, subkey);
    if (status == ERROR_FILE_NOT_FOUND) {
        return S_OK;
    }
    return HRESULT_FROM_WIN32(status);
}
}

BOOL APIENTRY DllMain(HMODULE module, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        g_module = module;
        DisableThreadLibraryCalls(module);
    }
    return TRUE;
}

extern "C" HRESULT __stdcall DllRegisterServer() {
    wchar_t path[MAX_PATH]{};
    if (!modulePath(path, MAX_PATH)) {
        return HRESULT_FROM_WIN32(GetLastError());
    }

    constexpr wchar_t clsidKey[] = L"Software\\Classes\\CLSID\\{4B6B66F3-0182-4E8B-9B7C-0C545022110A}";
    constexpr wchar_t inprocKey[] = L"Software\\Classes\\CLSID\\{4B6B66F3-0182-4E8B-9B7C-0C545022110A}\\InprocServer32";
    constexpr wchar_t asioKey[] = L"Software\\ASIO\\ASIOA Audio Router";

    HRESULT hr = setStringValue(HKEY_LOCAL_MACHINE, clsidKey, nullptr, L"ASIOA Audio Router");
    if (FAILED(hr)) return hr;
    hr = setStringValue(HKEY_LOCAL_MACHINE, inprocKey, nullptr, path);
    if (FAILED(hr)) return hr;
    hr = setStringValue(HKEY_LOCAL_MACHINE, inprocKey, L"ThreadingModel", L"Both");
    if (FAILED(hr)) return hr;
    hr = setStringValue(HKEY_LOCAL_MACHINE, asioKey, L"CLSID", L"{4B6B66F3-0182-4E8B-9B7C-0C545022110A}");
    if (FAILED(hr)) return hr;
    hr = setStringValue(HKEY_LOCAL_MACHINE, asioKey, L"Description", L"ASIOA Audio Router");
    return hr;
}

extern "C" HRESULT __stdcall DllUnregisterServer() {
    deleteTree(HKEY_LOCAL_MACHINE, L"Software\\ASIO\\ASIOA Audio Router");
    return deleteTree(HKEY_LOCAL_MACHINE, L"Software\\Classes\\CLSID\\{4B6B66F3-0182-4E8B-9B7C-0C545022110A}");
}
