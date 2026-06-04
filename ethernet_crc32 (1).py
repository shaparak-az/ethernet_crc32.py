"""
Ethernet CRC-32 / FCS Lab
=========================
Polynomial : 0x04C11DB7  (standard IEEE 802.3)
Reflected  : 0xEDB88320  (used in hardware / reflected algorithm)
"""

# ---------------------------------------------------------------------------
# Core CRC-32 engine
# ---------------------------------------------------------------------------

POLY_REFLECTED = 0xEDB88320


def crc32(data: bytes) -> int:
    """
    Compute the standard Ethernet CRC-32 over *data*.
    Uses the reflected (LSB-first) algorithm that matches NIC hardware.

    Returns a 32-bit unsigned integer.
    """
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ POLY_REFLECTED
            else:
                crc >>= 1
    return crc ^ 0xFFFFFFFF


def fcs_bytes(crc_value: int) -> bytes:
    """Return the 4-byte little-endian FCS for a given CRC-32 value."""
    return crc_value.to_bytes(4, byteorder='little')


# ---------------------------------------------------------------------------
# Part A — CRC generation
# ---------------------------------------------------------------------------

def generate_frame(raw_frame: bytes) -> bytes:
    """
    Part A: Given a raw Ethernet frame (without FCS), compute CRC-32
    and return the complete transmitted frame with FCS appended.

    Steps:
      1. Convert the header + payload into a byte stream.
      2. Compute the CRC-32 remainder using the generator polynomial.
      3. Append the 4-byte FCS (little-endian) to form the final frame.

    Parameters
    ----------
    raw_frame : bytes
        Frame bytes WITHOUT the FCS field
        (Destination MAC + Source MAC + EtherType + Payload).

    Returns
    -------
    bytes
        Complete transmitted frame (raw_frame + 4-byte FCS).
    """
    if len(raw_frame) < 14:
        raise ValueError("Frame too short: need at least 14 bytes (6+6+2).")

    crc  = crc32(raw_frame)
    fcs  = fcs_bytes(crc)
    return raw_frame + fcs


# ---------------------------------------------------------------------------
# Part B — CRC verification
# ---------------------------------------------------------------------------

# When CRC-32 is run over (data + correct FCS) the result is always this value.
ETHERNET_MAGIC_RESIDUE = 0x2144DF1C


def verify_frame(received_frame: bytes) -> dict:
    """
    Part B: Verify the integrity of a received Ethernet frame.

    Steps:
      1. Separate the received FCS (last 4 bytes) from the data.
      2. Re-compute CRC-32 over the data portion.
      3. Compare computed FCS directly against received FCS byte-by-byte.

    Parameters
    ----------
    received_frame : bytes
        Full received frame INCLUDING the 4-byte FCS at the end.

    Returns
    -------
    dict with keys:
        valid          (bool)   – True if frame is error-free
        received_fcs   (bytes)  – The FCS bytes extracted from the frame
        computed_fcs   (bytes)  – The FCS we would expect for this data
        decision       (str)    – "ACCEPT" or "DROP (frame corrupted)"
    """
    if len(received_frame) < 18:
        raise ValueError("Frame too short: need at least 18 bytes (14 header + 4 FCS).")

    data          = received_frame[:-4]
    received_fcs  = received_frame[-4:]

    computed_crc  = crc32(data)
    comp_fcs      = fcs_bytes(computed_crc)

    valid         = (received_fcs == comp_fcs)   # direct byte-by-byte comparison

    return {
        "valid":         valid,
        "received_fcs":  received_fcs,
        "computed_fcs":  comp_fcs,
        "decision":      "ACCEPT" if valid else "DROP (frame corrupted)",
    }


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def hex_to_bytes(hex_string: str) -> bytes:
    """Convert a hex string (spaces allowed) to bytes."""
    return bytes.fromhex(hex_string.replace(" ", ""))


def bytes_to_hex(data: bytes) -> str:
    """Return a spaced uppercase hex string."""
    return " ".join(f"{b:02X}" for b in data)


def print_frame_fields(frame: bytes, label: str = "Frame") -> None:
    """Pretty-print the fields of an Ethernet frame."""
    print(f"\n{'─'*60}")
    print(f"  {label}")
    print(f"{'─'*60}")
    if len(frame) < 14:
        print("  (too short to decode fields)")
        return
    print(f"  Destination MAC : {bytes_to_hex(frame[0:6])}")
    print(f"  Source MAC      : {bytes_to_hex(frame[6:12])}")
    ethertype = int.from_bytes(frame[12:14], 'big')
    et_name   = {0x0800: "IPv4", 0x0806: "ARP", 0x86DD: "IPv6",
                 0x8100: "802.1Q VLAN"}.get(ethertype, "")
    print(f"  EtherType       : 0x{ethertype:04X} {et_name}")
    payload   = frame[14:-4] if len(frame) > 18 else frame[14:]
    print(f"  Payload         : {bytes_to_hex(payload)}")
    if len(frame) >= 18:
        print(f"  FCS             : {bytes_to_hex(frame[-4:])}")
    print(f"{'─'*60}")


# ---------------------------------------------------------------------------
# Simple test suite
# ---------------------------------------------------------------------------

def run_tests() -> None:
    """
    A short test that covers:
      Test 1 – Part A  : generate FCS for an ARP request frame
      Test 2 – Part B  : verify the generated frame is accepted
      Test 3 – Part B  : verify a single-bit corruption is detected
    """
    print("=" * 60)
    print("  Ethernet CRC-32 Lab — Test Suite")
    print("=" * 60)

    # ── Raw ARP request frame (no FCS) ──────────────────────────────
    raw_hex = (
        "ff ff ff ff ff ff "   # dst MAC  (broadcast)
        "00 1a 2b 3c 4d 5e "   # src MAC
        "08 06 "               # EtherType ARP
        "00 01 08 00 06 04 00 01 "
        "00 1a 2b 3c 4d 5e c0 a8 01 01 "
        "00 00 00 00 00 00 c0 a8 01 64 "
        "00 00 00 00 00 00 00 00 00 00 "
        "00 00 00 00 00 00 00 00"
    )
    raw_frame = hex_to_bytes(raw_hex)

    # ── TEST 1: Part A – frame generation ───────────────────────────
    print("\n[ TEST 1 ]  Part A — generate FCS")
    transmitted = generate_frame(raw_frame)
    fcs = transmitted[-4:]
    print(f"  Input length   : {len(raw_frame)} bytes")
    print(f"  Output length  : {len(transmitted)} bytes")
    print(f"  Computed FCS   : {bytes_to_hex(fcs)}")
    print_frame_fields(transmitted, "Transmitted frame")

    # ── TEST 2: Part B – valid frame ────────────────────────────────
    print("\n[ TEST 2 ]  Part B — verify valid frame")
    result = verify_frame(transmitted)
    print(f"  Received FCS   : {bytes_to_hex(result['received_fcs'])}")
    print(f"  Computed FCS   : {bytes_to_hex(result['computed_fcs'])}")
    print(f"  Match          : {result['received_fcs'] == result['computed_fcs']}")
    print(f"  Decision       : {result['decision']}")
    assert result["valid"], "TEST 2 FAILED: valid frame rejected!"
    print("  ✓ PASS")

    # ── TEST 3: Part B – corrupted frame ────────────────────────────
    print("\n[ TEST 3 ]  Part B — detect single-byte corruption")
    corrupted = bytearray(transmitted)
    corrupted[20] ^= 0xFF                   # flip all bits in byte 20 (payload)
    result_bad = verify_frame(bytes(corrupted))
    print(f"  Received FCS   : {bytes_to_hex(result_bad['received_fcs'])}")
    print(f"  Computed FCS   : {bytes_to_hex(result_bad['computed_fcs'])}")
    print(f"  Match          : {result_bad['received_fcs'] == result_bad['computed_fcs']}")
    print(f"  Decision       : {result_bad['decision']}")
    assert not result_bad["valid"], "TEST 3 FAILED: corrupted frame accepted!"
    print("  ✓ PASS")

    print("\n" + "=" * 60)
    print("  All tests passed.")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_tests()
