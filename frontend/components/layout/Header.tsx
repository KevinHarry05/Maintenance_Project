'use client'

import Link from 'next/link'
import { Bell, Building2 } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function Header() {
  return (
    <header className="border-b border-blue-100 bg-white px-6 py-4">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <Building2 className="h-6 w-6 text-primary" />
          <span className="font-semibold text-foreground">SBMS</span>
        </Link>
        <Button variant="ghost" size="icon" aria-label="Open notifications">
          <Bell className="h-5 w-5" />
        </Button>
      </div>
    </header>
  )
}
