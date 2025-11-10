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


    
