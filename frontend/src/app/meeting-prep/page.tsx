import { ModulePlaceholder } from "@/components/module-placeholder";

export default function MeetingPrepPage() {
  return (
    <ModulePlaceholder
      title="Meeting Preparation Agent"
      description="Auto-generate agendas, talking points, key risks, open decisions, and follow-up actions."
      endpoint="/api/v1/meeting-prep/prepare"
    />
  );
}
