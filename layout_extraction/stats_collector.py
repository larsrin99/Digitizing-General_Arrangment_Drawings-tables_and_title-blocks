from __future__ import annotations
from dataclasses import dataclass, field
from statistics import mean

@dataclass
class StatsCollector:
    pages: int = 0
    h_lines: int = 0
    v_lines: int = 0
    rect_init: int = 0
    rect_merged: int = 0
    tables_with_text: int = 0
    dup_tables_removed: int = 0
    row_counts: list[int] = field(default_factory=list)
    col_counts: list[int] = field(default_factory=list)

    # Convenience helpers
    def add_line_counts(self, h: int, v: int) -> None:
        self.h_lines += h
        self.v_lines += v

    def add_rect_init(self, n: int) -> None:
        self.rect_init += n

    def add_rect_merged(self, n: int) -> None:
        self.rect_merged += n

    def add_table(self, rows: int, cols: int) -> None:
        self.tables_with_text += 1
        self.row_counts.append(rows)
        self.col_counts.append(cols)

    # Final dict for Tbl‑1
    def as_summary(self) -> dict[str, str | int | float]:
        return {
            "Pages processed": self.pages,
            "Total lines": f"{self.h_lines} / {self.v_lines}",
            "Rectangles initial": self.rect_init,
            "Rectangles retained": self.rect_merged,
            "Tables ≥1 rc": self.tables_with_text,
            "Duplicate tables removed": self.dup_tables_removed,
            "Avg rows per table": round(mean(self.row_counts), 2) if self.row_counts else 0,
            "Avg cols per table": round(mean(self.col_counts), 2) if self.col_counts else 0,
        }