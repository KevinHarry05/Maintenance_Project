'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

type SidebarItem = {
  label: string
  href: string
}

export function Sidebar({ items }: { items: SidebarItem[] }) {
  const pathname = usePathname()

  return (
    <aside className="w-64 border-r border-blue-100 bg-white p-4">
      <nav className="space-y-1">
        {items.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'block rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-blue-50 hover:text-primary',
              pathname === item.href && 'bg-blue-100 text-primary',
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  )
}
