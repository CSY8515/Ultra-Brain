import type { Metadata } from "next";
import { UltraBrainShell } from "./ultra-brain-shell";

export const metadata: Metadata = {
  title: "Ultra Brain v0.94",
  description: "Ultra Brain User Custom UI and Canvas Editor",
};

export default function Home() {
  return <UltraBrainShell />;
}
