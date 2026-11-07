export function AmbientBackground() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden"
    >
      <div className="absolute -left-40 -top-40 h-96 w-96 rounded-full bg-neon-pink/10 blur-[100px]" />
      <div className="absolute -right-40 top-1/4 h-96 w-96 rounded-full bg-neon-cyan/15 blur-[110px]" />
      <div className="absolute bottom-20 left-1/3 h-72 w-[500px] rounded-full bg-neon-purple/10 blur-[120px]" />
      <div className="absolute inset-0 bg-grid opacity-[0.025]" />
    </div>
  );
}
