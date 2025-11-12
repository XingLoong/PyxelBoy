import json
from pathlib import Path
from instructions import Instruction, Operand

def load_opcodes(opcode_file):
    try:
        with open(opcode_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Opcode file not found: {opcode_file}")
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in opcode file: {error}")
    
    prefixed = {}
    regular = {}
    
    # Process unprefixed opcodes
    if "unprefixed" in data:
        for opcode, entry in data["unprefixed"].items():
            _process_opcode(opcode, entry, regular, is_prefixed=False)
    
    # Process CB-prefixed opcodes
    if "cbprefixed" in data:
        for opcode, entry in data["cbprefixed"].items():
            _process_opcode(opcode, entry, prefixed, is_prefixed=True)
    
    return prefixed, regular

def _process_opcode(opcode: str, entry: dict, target: dict, is_prefixed: bool):
    # Parse opcode
    opcode_str = opcode.lower().replace("0x", "")
    try:
        opcode_int = int(opcode_str, 16)
    except ValueError:
        print(f"Warning: Skipping invalid hex opcode: {opcode}")
        return
    
    # Build operands
    operands = [
        Operand(
            name=op.get("name", "UNKNOWN"),
            bytes=op.get("bytes", 0),
            immediate=op.get("immediate", False),
            value=op.get("value"),
            adjust=op.get("adjust")
        )
        for op in entry.get("operands", [])
    ]
    
    # Handle cycles (can be int or list)
    cycles_entry = entry.get("cycles", 0)
    cycles = cycles_entry if isinstance(cycles_entry, list) else [cycles_entry]
    
    # Create instruction
    instr = Instruction(
        opcode=opcode_int,
        mnemonic=entry.get("mnemonic", f"UNKNOWN_{opcode}"),
        bytes=entry.get("bytes", 1),
        cycles=cycles,
        operands=operands,
        immediate=entry.get("immediate", False),
        flags=entry.get("flags"),
        comment=entry.get("comment", "")
    )
    
    target[opcode_int] = instr


if __name__ == "__main__":
    from pprint import pprint

    # Example test file path
    opcode_path = Path("data/Opcodes.json")

    # Load and test
    prefixed, regular = load_opcodes(opcode_path)

    print("\n=== Regular Opcodes (first 5) ===")
    for opcode_int in sorted(regular.keys())[:5]:
        instr = regular[opcode_int]
        print(f"0x{opcode_int:02X}: {instr.mnemonic} (bytes={instr.bytes}, cycles={instr.cycles})")

    print("\n=== Prefixed Opcodes (first 5) ===")
    for opcode_int in sorted(prefixed.keys())[:5]:
        instr = prefixed[opcode_int]
        print(f"0xCB{opcode_int:02X}: {instr.mnemonic} (bytes={instr.bytes}, cycles={instr.cycles})")
    pprint(regular[0x01])
    pprint(regular[0x01].mnemonic)
    pprint(regular[0x01].operands)
    # pprint(dict(list(regular.items())[:5]))
