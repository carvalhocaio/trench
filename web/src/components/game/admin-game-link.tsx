import Link from "next/link";

export function AdminGameLink({ gameId }: { gameId: string }) {
  return (
    <Link
      href={`/admin/games/${gameId}`}
      className="text-sm font-medium text-nfl-navy hover:underline"
    >
      Editar cadastro deste jogo →
    </Link>
  );
}
