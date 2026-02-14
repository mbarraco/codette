import type { ReactNode } from "react";

type DataTableProps = {
  loading: boolean;
  empty: boolean;
  emptyMessage?: string;
  children: ReactNode;
};

function DataTable({
  loading,
  empty,
  emptyMessage = "No items.",
  children,
}: DataTableProps) {
  if (loading) return <p>Loading...</p>;
  if (empty) return <p>{emptyMessage}</p>;
  return <>{children}</>;
}

export default DataTable;
