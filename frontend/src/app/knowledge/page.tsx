import { ModulePlaceholder } from "@/components/module-placeholder";

export default function KnowledgePage() {
  return (
    <ModulePlaceholder
      title="Engineering Knowledge Hub"
      description="Semantic + RAG search across your uploaded documents, standards, and reports."
      endpoint="/api/v1/knowledge/search"
    />
  );
}
