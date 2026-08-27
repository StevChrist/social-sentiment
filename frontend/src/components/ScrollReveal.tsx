// src/components/ScrollReveal.tsx
"use client";

import React, { useEffect, useRef, useState } from 'react';

interface ScrollRevealProps {
  children: React.ReactNode;
  variant?: 'fade-up' | 'fade-down' | 'fade-left' | 'fade-right' | 'scale-up' | 'blur-in';
  delay?: number; // delay in milliseconds
  duration?: number; // duration in milliseconds
  threshold?: number;
  className?: string;
  style?: React.CSSProperties;
}

export default function ScrollReveal({
  children,
  variant = 'fade-up',
  delay = 0,
  duration = 700,
  threshold = 0.15,
  className = '',
  style = {},
}: ScrollRevealProps): React.ReactElement {
  const [isVisible, setIsVisible] = useState(false);
  const domRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
            // Once visible, keep it visible
            if (domRef.current) observer.unobserve(domRef.current);
          }
        });
      },
      {
        threshold,
        rootMargin: '0px 0px -50px 0px',
      }
    );

    const currentElem = domRef.current;
    if (currentElem) {
      observer.observe(currentElem);
    }

    return () => {
      if (currentElem) {
        observer.unobserve(currentElem);
      }
    };
  }, [threshold]);

  const getInitialTransform = () => {
    switch (variant) {
      case 'fade-up':
        return 'translateY(40px)';
      case 'fade-down':
        return 'translateY(-40px)';
      case 'fade-left':
        return 'translateX(-40px)';
      case 'fade-right':
        return 'translateX(40px)';
      case 'scale-up':
        return 'scale(0.92) translateY(20px)';
      case 'blur-in':
        return 'scale(0.96)';
      default:
        return 'translateY(30px)';
    }
  };

  const getInitialFilter = () => {
    if (variant === 'blur-in') return 'blur(10px)';
    return 'none';
  };

  const dynamicStyle: React.CSSProperties = {
    opacity: isVisible ? 1 : 0,
    transform: isVisible ? 'translate(0, 0) scale(1)' : getInitialTransform(),
    filter: isVisible ? 'none' : getInitialFilter(),
    transition: `opacity ${duration}ms cubic-bezier(0.16, 1, 0.3, 1) ${delay}ms, transform ${duration}ms cubic-bezier(0.16, 1, 0.3, 1) ${delay}ms, filter ${duration}ms ease-out ${delay}ms`,
    willChange: 'opacity, transform, filter',
    ...style,
  };

  return (
    <div ref={domRef} className={className} style={dynamicStyle}>
      {children}
    </div>
  );
}
