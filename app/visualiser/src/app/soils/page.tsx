import { RetentionViewer } from "@/c/RetentionViewer";
import { SoilColumnViewer } from "@/c/SoilColumnViewer";
import { TextureTriangleViewer } from "@/c/TextureTriangleViewer";

export default function SoilsPage() {
  return (
    <>
      <RetentionViewer />
      <TextureTriangleViewer />
      <SoilColumnViewer />
    </>
  );
}
