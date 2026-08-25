import { ModulePlaceholder } from "@/components/module-placeholder";

export default function DesignReviewPage() {
  return (
    <ModulePlaceholder
      title="Design Review Agent"
      description="Generate review checklists, surface engineering risks, missing info, and improvements."
      endpoint="/api/v1/design-review/review"
    />
  );
}
