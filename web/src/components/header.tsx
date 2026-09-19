import Link from "next/link";

const NAV_LINKS = [
  { href: "/", label: "Semana" },
  { href: "/highlights", label: "Destaques" },
  { href: "/admin", label: "Cadastro" },
] as const;

export function Header() {
  return (
    <header className="border-b-4 border-nfl-red bg-nfl-navy text-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
        <Link href="/" className="font-black text-xl tracking-widest">
          TRENCH
        </Link>
        <nav className="flex gap-6 text-sm font-medium">
          {NAV_LINKS.map((link) => (
            <Link key={link.href} href={link.href} className="hover:text-zinc-200">
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
