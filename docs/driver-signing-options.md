# ASIOA Windows Driver Signing Options

ASIOA has two different Windows driver surfaces:

- ASIO COM driver: visible to ASIO-capable hosts through `HKLM\SOFTWARE\ASIO\ASIOA Audio Router`.
- Windows endpoint driver: visible to normal WDM, WASAPI, and DirectSound applications as speaker and microphone devices.

The ASIO COM driver can be registered locally. The Windows endpoint driver is a kernel-mode package, so Windows 10 and later will not load it on normal Secure Boot systems unless it is trusted by Microsoft's driver-signing chain.

## Current Blocker

If Device Manager or `pnputil` reports Code 52 for `ASIOA Audio Router Bridge`, Windows sees the endpoint but refuses to load it because the package is not trusted by the current boot-signing policy.

Administrator permission can install, remove, or repair the package. Administrator permission cannot make an unsigned or locally test-signed kernel endpoint load on a normal Secure Boot machine.

## Legal Paths

### 1. Free Development Test Signing

Use this only on development machines.

What it does:

- Creates or uses a local test certificate.
- Test-signs the endpoint package catalog.
- Enables Windows test-signing mode.
- Reboots, then reinstalls the endpoint driver.

Important limits:

- This is not for public users.
- Secure Boot usually must be disabled before TESTSIGNING can be enabled.
- The desktop will normally show Windows Test Mode.
- This path proves the endpoint architecture, but it is not a release signature.

Useful commands for an elevated development shell:

```powershell
bcdedit /set testsigning on
.\scripts\build-endpoint-driver.ps1
.\scripts\install-asioa-endpoint-driver.ps1
.\scripts\check-driver-signing-state.ps1
```

To leave test mode later:

```powershell
bcdedit /set testsigning off
```

Reboot after changing TESTSIGNING either way.

### 2. Microsoft Preproduction Signing

Use this for partner test machines that must keep Secure Boot enabled during validation.

What it does:

- Submits a preproduction driver through Microsoft Hardware Dev Center.
- Provisions specific test machines to trust Microsoft's preproduction Secure Boot policy.
- Allows Secure Boot testing before production release.

Important limits:

- It is still not a normal public release path.
- Test machines must be explicitly provisioned.
- It requires Hardware Dev Center access.

### 3. Partner Center Attestation Signing

Use this for the fastest normal production signing path.

What it does:

- Packages the endpoint INF, SYS, CAT, and symbols into a CAB.
- Signs the CAB with an EV code-signing certificate.
- Submits the CAB through Microsoft Partner Center.
- Microsoft returns a package with a Microsoft-signed catalog.

Important limits:

- The Microsoft Hardware Developer Program requires an EV code-signing certificate.
- Attestation is lighter than full HLK/WHQL, but still requires the Microsoft submission path.
- This is the likely first public release path for ASIOA endpoint devices.

Current helper:

```powershell
.\scripts\package-endpoint-driver-submission.ps1
```

### 4. HLK/WHQL Signing

Use this for the strongest certification path.

What it does:

- Runs Windows Hardware Lab Kit tests.
- Produces an HLKX package.
- Submits the driver for Windows Hardware Compatibility Program certification.

Important limits:

- More work than attestation.
- Requires suitable test machines and passing HLK tests.
- Best long-term path if ASIOA should be broadly trusted, enterprise-friendly, or distributed through Windows Update.

## Practical Release Plan

1. Keep ASIO COM driver working for ASIO-capable hosts.
2. Use free test-signing only on ASIOA development machines to prove the endpoint audio path.
3. Finish the endpoint driver's real audio transport and feedback guard while using test mode.
4. Submit the endpoint CAB through Partner Center attestation for the first public signed endpoint.
5. Move to HLK/WHQL after the endpoint behavior is stable enough for certification testing.

## References

- Microsoft driver signing options: https://learn.microsoft.com/en-us/windows-hardware/drivers/dashboard/driver-signing-offerings
- Microsoft attestation signing: https://learn.microsoft.com/en-us/windows-hardware/drivers/dashboard/code-signing-attestation
- Microsoft driver code-signing requirements: https://learn.microsoft.com/en-us/windows-hardware/drivers/dashboard/code-signing-reqs
- Microsoft test-signing option: https://learn.microsoft.com/en-us/windows-hardware/drivers/install/the-testsigning-boot-configuration-option
- Microsoft preproduction signing with Secure Boot: https://learn.microsoft.com/en-us/windows-hardware/drivers/install/preproduction-driver-signing-and-install
