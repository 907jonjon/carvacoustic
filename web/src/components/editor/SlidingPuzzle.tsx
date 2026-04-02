"use client";

import { useState, useCallback, useEffect } from "react";

const SIZE = 4;
const TOTAL = SIZE * SIZE;

function createSolvedBoard(): number[] {
  return Array.from({ length: TOTAL }, (_, i) => (i + 1) % TOTAL);
}

function shuffle(board: number[]): number[] {
  const b = [...board];
  let empty = b.indexOf(0);
  for (let i = 0; i < 200; i++) {
    const neighbors = getMovableTiles(empty);
    const pick = neighbors[Math.floor(Math.random() * neighbors.length)];
    [b[empty], b[pick]] = [b[pick], b[empty]];
    empty = pick;
  }
  return b;
}

function getMovableTiles(emptyIdx: number): number[] {
  const row = Math.floor(emptyIdx / SIZE);
  const col = emptyIdx % SIZE;
  const neighbors: number[] = [];
  if (row > 0) neighbors.push((row - 1) * SIZE + col);
  if (row < SIZE - 1) neighbors.push((row + 1) * SIZE + col);
  if (col > 0) neighbors.push(row * SIZE + col - 1);
  if (col < SIZE - 1) neighbors.push(row * SIZE + col + 1);
  return neighbors;
}

function isSolved(board: number[]): boolean {
  for (let i = 0; i < TOTAL; i++) {
    if (board[i] !== (i + 1) % TOTAL) return false;
  }
  return true;
}

export function SlidingPuzzle({ onDismiss }: { onDismiss?: () => void }) {
  const [board, setBoard] = useState(() => shuffle(createSolvedBoard()));
  const [moves, setMoves] = useState(0);
  const [solved, setSolved] = useState(false);

  useEffect(() => {
    setSolved(isSolved(board));
  }, [board]);

  const handleClick = useCallback((idx: number) => {
    if (solved) return;
    const emptyIdx = board.indexOf(0);
    if (!getMovableTiles(emptyIdx).includes(idx)) return;
    setBoard((prev) => {
      const next = [...prev];
      [next[emptyIdx], next[idx]] = [next[idx], next[emptyIdx]];
      return next;
    });
    setMoves((m) => m + 1);
  }, [board, solved]);

  const handleShuffle = useCallback(() => {
    setBoard(shuffle(createSolvedBoard()));
    setMoves(0);
    setSolved(false);
  }, []);

  return (
    <div className="flex flex-col items-center gap-3">
      <p className="text-sm text-gray-500">
        While your design is being prepared...
      </p>
      <div
        className="grid gap-1 rounded-lg bg-gray-200 p-2"
        style={{
          gridTemplateColumns: `repeat(${SIZE}, 1fr)`,
          width: `${SIZE * 68 + (SIZE - 1) * 4 + 16}px`,
        }}
      >
        {board.map((tile, idx) => (
          <button
            key={idx}
            onClick={() => handleClick(idx)}
            disabled={tile === 0}
            className={`flex h-16 w-16 items-center justify-center rounded text-lg font-bold transition-all duration-150 ${
              tile === 0
                ? "bg-transparent"
                : "cursor-pointer border border-brand-200 bg-brand-50 text-brand-700 hover:bg-brand-100 active:scale-95"
            }`}
          >
            {tile !== 0 ? tile : ""}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-4 text-xs text-gray-400">
        <span>{moves} moves</span>
        {solved && (
          <span className="font-medium text-green-600">Solved!</span>
        )}
        <button
          onClick={handleShuffle}
          className="rounded px-2 py-1 text-xs text-gray-500 hover:bg-gray-100"
        >
          Shuffle
        </button>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="rounded px-2 py-1 text-xs text-gray-500 hover:bg-gray-100"
          >
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
}
