"use client";

import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { RefreshCw } from "lucide-react";
import { useDeferredValue, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Opportunity, listOpportunities } from "@/lib/backend-api";
import { cn } from "@/lib/utils";

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

function statusClassName(status: Opportunity["status"]) {
  switch (status) {
    case "applied":
    case "interviewing":
    case "offer":
      return "bg-emerald-50 text-emerald-700 ring-emerald-600/20";
    case "rejected":
    case "archived":
      return "bg-gray-50 text-gray-600 ring-gray-500/20";
    case "interested":
      return "bg-blue-50 text-blue-700 ring-blue-600/20";
    default:
      return "bg-amber-50 text-amber-700 ring-amber-600/20";
  }
}

export function OpportunitiesTable() {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [search, setSearch] = useState("");
  const [appliedFilter, setAppliedFilter] = useState<"all" | "yes" | "no">(
    "all",
  );
  const [minimumScore, setMinimumScore] = useState("");
  const deferredSearch = useDeferredValue(search);
  const opportunitiesQuery = useQuery({
    queryKey: ["opportunities"],
    queryFn: listOpportunities,
    refetchInterval: 10_000,
  });

  const columns = useMemo<ColumnDef<Opportunity>[]>(
    () => [
      {
        accessorKey: "title",
        header: "Role",
        cell: ({ row }) => (
          <div className="min-w-0">
            <div className="truncate font-medium text-foreground">
              {row.original.title || "Untitled role"}
            </div>
            {row.original.url ? (
              <a
                href={row.original.url}
                target="_blank"
                rel="noreferrer"
                className="block truncate text-xs text-muted-foreground hover:text-foreground"
              >
                {row.original.url}
              </a>
            ) : null}
          </div>
        ),
      },
      {
        accessorKey: "company",
        header: "Company",
        cell: ({ row }) => row.original.company || "-",
      },
      {
        accessorKey: "location",
        header: "Location",
        cell: ({ row }) => row.original.location || "-",
      },
      {
        accessorKey: "score",
        header: "Score",
        cell: ({ row }) => (
          <span className="font-medium tabular-nums">
            {row.original.score == null ? "-" : `${row.original.score}/25`}
          </span>
        ),
      },
      {
        accessorKey: "applied",
        header: "Applied",
        cell: ({ row }) => (
          <span
            className={cn(
              "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset",
              row.original.applied
                ? "bg-emerald-50 text-emerald-700 ring-emerald-600/20"
                : "bg-gray-50 text-gray-600 ring-gray-500/20",
            )}
          >
            {row.original.applied ? "Yes" : "No"}
          </span>
        ),
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => (
          <span
            className={cn(
              "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset",
              statusClassName(row.original.status),
            )}
          >
            {row.original.status}
          </span>
        ),
      },
      {
        accessorKey: "updated_at",
        header: "Updated",
        cell: ({ row }) => formatDate(row.original.updated_at),
      },
    ],
    [],
  );

  const filteredOpportunities = useMemo(() => {
    const normalizedSearch = deferredSearch.trim().toLowerCase();
    const minimumScoreValue = minimumScore ? Number(minimumScore) : null;

    return (opportunitiesQuery.data ?? []).filter((opportunity) => {
      if (appliedFilter === "yes" && !opportunity.applied) return false;
      if (appliedFilter === "no" && opportunity.applied) return false;
      if (
        minimumScoreValue !== null &&
        Number.isFinite(minimumScoreValue) &&
        (opportunity.score ?? -1) < minimumScoreValue
      ) {
        return false;
      }

      if (!normalizedSearch) return true;

      return [
        opportunity.title,
        opportunity.company,
        opportunity.location,
        opportunity.url,
        opportunity.status,
      ]
        .filter(Boolean)
        .some((value) => value?.toLowerCase().includes(normalizedSearch));
    });
  }, [appliedFilter, deferredSearch, minimumScore, opportunitiesQuery.data]);

  const table = useReactTable({
    data: filteredOpportunities,
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <Card className="h-full gap-4 overflow-hidden py-0">
      <CardHeader className="border-b px-4 py-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle>Opportunities</CardTitle>
            <CardDescription>
              Jobs tracked by the agent, refreshed every 10 seconds.
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => opportunitiesQuery.refetch()}
            disabled={opportunitiesQuery.isFetching}
          >
            <RefreshCw
              className={cn(
                "size-4",
                opportunitiesQuery.isFetching && "animate-spin",
              )}
            />
            Refresh
          </Button>
        </div>
        <div className="grid gap-2 pt-3 md:grid-cols-[minmax(0,1fr)_120px_120px]">
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search roles, companies, locations..."
            className="bg-background"
          />
          <select
            value={appliedFilter}
            onChange={(event) =>
              setAppliedFilter(event.target.value as "all" | "yes" | "no")
            }
            className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-xs"
          >
            <option value="all">All applied</option>
            <option value="yes">Applied</option>
            <option value="no">Not applied</option>
          </select>
          <Input
            type="number"
            min={0}
            max={25}
            value={minimumScore}
            onChange={(event) => setMinimumScore(event.target.value)}
            placeholder="Min score"
            className="bg-background"
          />
        </div>
      </CardHeader>
      <CardContent className="min-h-0 flex-1 overflow-auto p-0">
        {opportunitiesQuery.isError ? (
          <div className="p-4 text-sm text-destructive">
            {(opportunitiesQuery.error as Error).message}
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 z-10 border-b bg-background text-xs uppercase text-muted-foreground">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="whitespace-nowrap px-4 py-3 font-medium"
                    >
                      {header.isPlaceholder ? null : (
                        <button
                          type="button"
                          className="text-left hover:text-foreground"
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                          {{
                            asc: " ↑",
                            desc: " ↓",
                          }[header.column.getIsSorted() as string] ?? null}
                        </button>
                      )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="divide-y">
              {table.getRowModel().rows.length ? (
                table.getRowModel().rows.map((row) => (
                  <tr key={row.id} className="hover:bg-muted/40">
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="max-w-64 px-4 py-3">
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext(),
                        )}
                      </td>
                    ))}
                  </tr>
                ))
              ) : (
                <tr>
                  <td
                    colSpan={columns.length}
                    className="px-4 py-10 text-center text-sm text-muted-foreground"
                  >
                    {opportunitiesQuery.isLoading
                      ? "Loading opportunities..."
                      : "No opportunities yet. Paste jobs into chat to get started."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </CardContent>
    </Card>
  );
}

