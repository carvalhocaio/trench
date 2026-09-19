import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center gap-4 rounded-lg border border-zinc-200 bg-white p-8 text-center">
      <h1 className="text-lg font-semibold text-nfl-navy">Não encontrado</h1>
      <p className="text-sm text-zinc-600">
        O conteúdo que você procura não existe ou foi removido.
      </p>
      <Link
        href="/"
        className="rounded-md bg-nfl-navy px-4 py-2 text-sm font-medium text-white hover:opacity-90"
      >
        Voltar para a semana
      </Link>
    </div>
  );
}
