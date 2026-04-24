import { api } from "@/lib/api/client";
import { StyleGrid } from "@/components/styles/StyleGrid";
import { EmptyState } from "@/components/common/EmptyState";

export const dynamic = "force-dynamic";

export default async function StylesPage() {
  try {
    const { styles } = await api.getStyles();
    return (
      <div className="mx-auto flex min-w-0 max-w-6xl flex-col gap-4">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">Style bank</h2>
          <p className="text-sm text-muted-foreground">
            {styles.length} styles indexed. Each card is embedded with MiniLM and
            searchable via FAISS.
          </p>
        </div>
        <StyleGrid styles={styles} />
      </div>
    );
  } catch (e) {
    return (
      <EmptyState
        title="Could not load styles"
        description={e instanceof Error ? e.message : String(e)}
      />
    );
  }
}
