export const metadata = {
  title: "OmniRate",
  description: "Polymorphic Rating & Proof-of-Experience Engine",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="mn">
      <body>{children}</body>
    </html>
  );
}
