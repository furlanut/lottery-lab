interface NumberBallProps {
  number: number;
  size?: "sm" | "md" | "lg" | "xl";
  glow?: boolean;
}

function getDecadeGradient(n: number): string {
  if (n <= 10) return "bg-gradient-to-br from-blue-500 to-blue-700";
  if (n <= 20) return "bg-gradient-to-br from-emerald-500 to-emerald-700";
  if (n <= 30) return "bg-gradient-to-br from-orange-500 to-orange-700";
  if (n <= 40) return "bg-gradient-to-br from-rose-500 to-rose-700";
  if (n <= 50) return "bg-gradient-to-br from-violet-500 to-violet-700";
  if (n <= 60) return "bg-gradient-to-br from-pink-500 to-pink-700";
  if (n <= 70) return "bg-gradient-to-br from-cyan-500 to-cyan-700";
  if (n <= 80) return "bg-gradient-to-br from-amber-500 to-amber-700";
  return "bg-gradient-to-br from-indigo-500 to-indigo-700";
}

function getGlowColor(n: number): string {
  if (n <= 10) return "shadow-blue-500/40";
  if (n <= 20) return "shadow-emerald-500/40";
  if (n <= 30) return "shadow-orange-500/40";
  if (n <= 40) return "shadow-rose-500/40";
  if (n <= 50) return "shadow-violet-500/40";
  if (n <= 60) return "shadow-pink-500/40";
  if (n <= 70) return "shadow-cyan-500/40";
  if (n <= 80) return "shadow-amber-500/40";
  return "shadow-indigo-500/40";
}

const sizeMap = {
  sm: { cls: "w-8 h-8 text-xs", style: { fontSize: "11px" } },
  md: { cls: "w-11 h-11 text-sm", style: {} },
  lg: { cls: "w-16 h-16 text-xl", style: {} },
  xl: { cls: "w-20 h-20 text-2xl", style: {} },
};

export default function NumberBall({
  number,
  size = "md",
  glow = false,
}: NumberBallProps) {
  const { cls } = sizeMap[size];
  const gradient = getDecadeGradient(number);
  const glowCls = glow ? `shadow-lg ${getGlowColor(number)}` : "";

  return (
    <span
      className={`lottery-ball ${gradient} ${cls} ${glowCls}`}
      aria-label={`Numero ${number}`}
    >
      {number}
    </span>
  );
}
