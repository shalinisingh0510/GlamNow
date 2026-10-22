import { ProfileClient } from "./profile-client";

interface PageProps {
  params: Promise<{ id: string }>;
}

export function generateStaticParams() {
  return [
    { id: "pro_1" },
    { id: "pro_2" },
    { id: "pro_3" },
    { id: "pro_4" },
  ];
}

export default async function ProfessionalProfilePage({ params }: PageProps) {
  const { id } = await params;
  return <ProfileClient id={id} />;
}
