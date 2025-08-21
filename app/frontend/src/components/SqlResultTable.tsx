import { DetailsList, IColumn } from "@fluentui/react";

interface SqlResultTableProps {
    rows: Record<string, unknown>[];
}

export const SqlResultTable = ({ rows }: SqlResultTableProps) => {
    if (!rows || rows.length === 0) {
        return null;
    }

    const columns: IColumn[] = Object.keys(rows[0]).map(key => ({
        key,
        name: key,
        fieldName: key,
        minWidth: 50,
        isResizable: true
    }));

    return <DetailsList items={rows} columns={columns} />;
};
