"use client";

import { Thread } from "@/components/thread";
import { StreamProvider } from "@/providers/Stream";
import { ThreadProvider } from "@/providers/Thread";
import { Toaster } from "@/components/ui/sonner";
import { OpportunitiesTable } from "@/components/opportunities-table";
import { AppQueryProvider } from "@/providers/query";
import React, { useEffect, useState } from "react";

const DEFAULT_TABLE_WIDTH = 42;
const MIN_TABLE_WIDTH = 28;
const MAX_TABLE_WIDTH = 65;

function useResizableTableWidth() {
  const [tableWidth, setTableWidth] = useState(DEFAULT_TABLE_WIDTH);

  useEffect(() => {
    const stored = window.localStorage.getItem("job-search-agent:table-width");
    if (!stored) return;

    const parsed = Number(stored);
    if (
      Number.isFinite(parsed) &&
      parsed >= MIN_TABLE_WIDTH &&
      parsed <= MAX_TABLE_WIDTH
    ) {
      setTableWidth(parsed);
    }
  }, []);

  const startResize = (event: React.PointerEvent<HTMLDivElement>) => {
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = tableWidth;

    const handleMove = (moveEvent: PointerEvent) => {
      const viewportWidth = window.innerWidth;
      const deltaPercent = ((startX - moveEvent.clientX) / viewportWidth) * 100;
      const nextWidth = Math.min(
        MAX_TABLE_WIDTH,
        Math.max(MIN_TABLE_WIDTH, startWidth + deltaPercent),
      );
      setTableWidth(nextWidth);
      window.localStorage.setItem(
        "job-search-agent:table-width",
        String(nextWidth),
      );
    };

    const handleUp = () => {
      window.removeEventListener("pointermove", handleMove);
      window.removeEventListener("pointerup", handleUp);
    };

    window.addEventListener("pointermove", handleMove);
    window.addEventListener("pointerup", handleUp);
  };

  return { tableWidth, startResize };
}

export default function DemoPage(): React.ReactNode {
  const { tableWidth, startResize } = useResizableTableWidth();

  return (
    <React.Suspense fallback={<div>Loading (layout)...</div>}>
      <Toaster />
      <AppQueryProvider>
        <ThreadProvider>
          <StreamProvider>
            <main
              className="grid h-screen grid-cols-1 overflow-hidden bg-muted/30 xl:grid-cols-[minmax(0,1fr)_6px_minmax(360px,var(--table-width))]"
              style={
                {
                  "--table-width": `${tableWidth}vw`,
                } as React.CSSProperties
              }
            >
              <section className="min-h-0 min-w-0 border-r bg-background">
                <Thread />
              </section>
              <div
                role="separator"
                aria-label="Resize opportunities panel"
                aria-orientation="vertical"
                className="hidden cursor-col-resize bg-border transition hover:bg-primary/40 xl:block"
                onPointerDown={startResize}
              />
              <aside className="hidden min-h-0 overflow-hidden p-4 xl:block">
                <OpportunitiesTable />
              </aside>
            </main>
          </StreamProvider>
        </ThreadProvider>
      </AppQueryProvider>
    </React.Suspense>
  );
}
