'use client';

import { useEffect, useState } from 'react';
import Button from "@/components/ui/Button";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      <h1 className="text-3xl font-bold underline">
        Hello world!
      </h1>
      <Button variant="primary">Test Button</Button>
    </div>
  )
}
