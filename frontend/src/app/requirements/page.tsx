import { ModulePlaceholder } from "@/components/module-placeholder";

export default function RequirementsPage() {
  return (
    <ModulePlaceholder
      title="Requirements Intelligence Agent"
      description="Detect contradictions, missing requirements, duplicates, and risks with traceability."
      endpoint="/api/v1/requirements/review"
    />
  );
}
