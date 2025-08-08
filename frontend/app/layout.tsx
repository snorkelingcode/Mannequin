import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Mannequin - Interactive 3D Character Customization',
  description: 'Customize your 3D mannequin with real-time controls, outfits, expressions, and more. Powered by Unreal Engine and streamed via Livepeer.',
  keywords: 'mannequin, 3d character, customization, unreal engine, streaming, livepeer',
  authors: [{ name: 'Mannequin Team' }],
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <div id="root">
          {children}
        </div>
      </body>
    </html>
  )
}