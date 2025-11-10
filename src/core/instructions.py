from dataclasses import dataclass
from typing import Literal, Optional, List, Dict

@dataclass(frozen=True)
class Operand:
    name: str
    bytes: int
    immediate: bool
    value: Optional[int]
    adjust: Optional[Literal["+", "-"]]

    def create(self, value):
        return Operand(
            name=self.name,
            bytes=self.bytes,
            immediate=self.immediate,
            value=value,
            adjust=self.adjust,
        )

@dataclass
class Instruction:
    opcode: int
    mnemonic: str
    bytes: int
    cycles: List[int]
    operands: List[Operand]
    immediate: bool
    flags: Optional[Dict[str, str]] = None
    comment: str = ""

    def create(self, operands: List[Operand]):
        return Instruction(
            opcode=self.opcode,
            mnemonic=self.mnemonic,
            bytes=self.bytes,
            cycles=self.cycles,
            immediate=self.immediate,
            operands=operands,
            flags=self.flags,
        )
