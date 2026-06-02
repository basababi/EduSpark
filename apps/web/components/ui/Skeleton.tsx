type SkeletonProps = {
  className?: string;
};

export function Skeleton({ className = "" }: SkeletonProps) {
  return <div className={`motion-safe:animate-pulse rounded-lg bg-neutral-200/80 ${className}`} />;
}
