'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ArrowRight, Building2, ChevronLeft, ChevronRight, Star, CheckCircle } from 'lucide-react';

const campusImages = [
  { src: '/college-modern.jpg', alt: 'Modern Building', title: 'Contemporary Architecture' },
  { src: '/college-auditorium.jpg', alt: 'Auditorium', title: 'State-of-the-Art Facilities' },
  { src: '/college-gate.jpg', alt: 'Campus Gate', title: '30-Year Legacy' },
  { src: '/college-campus.jpg', alt: 'Campus Aerial', title: 'Sprawling Campus' },
  { src: '/college-blue-building.jpg', alt: 'Blue Building', title: 'Modern Innovation' },
];

export default function Home() {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % campusImages.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  const nextImage = () => {
    setCurrentImageIndex((prev) => (prev + 1) % campusImages.length);
  };

  const prevImage = () => {
    setCurrentImageIndex((prev) => (prev - 1 + campusImages.length) % campusImages.length);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Navigation Header */}
      <nav className="fixed top-0 w-full bg-white/95 backdrop-blur-sm border-b border-blue-100 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center shadow-md">
              <Building2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="text-lg font-bold text-primary">SBMS</span>
              <p className="text-xs text-muted-foreground">St. Joseph&apos;s College</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" className="text-foreground hover:bg-blue-50">
                Login
              </Button>
            </Link>
            <Link href="/register">
              <Button className="bg-primary hover:bg-blue-700 text-white px-6">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Image Carousel Hero */}
      <section className="pt-20 pb-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="relative h-96 rounded-2xl overflow-hidden shadow-2xl border border-blue-100">
            <Image
              src={campusImages[currentImageIndex].src}
              alt={campusImages[currentImageIndex].alt}
              fill
              className="object-cover"
              priority
            />
            
            {/* Carousel Title Overlay */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-6">
              <h2 className="text-3xl font-bold text-white">{campusImages[currentImageIndex].title}</h2>
            </div>

            {/* Carousel Controls */}
            <button
              onClick={prevImage}
              className="absolute left-4 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white text-foreground p-2 rounded-full transition-all shadow-lg"
              aria-label="Previous image"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
            <button
              onClick={nextImage}
              className="absolute right-4 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white text-foreground p-2 rounded-full transition-all shadow-lg"
              aria-label="Next image"
            >
              <ChevronRight className="w-6 h-6" />
            </button>

            {/* Carousel Indicators */}
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
              {campusImages.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setCurrentImageIndex(idx)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    idx === currentImageIndex ? 'bg-white w-6' : 'bg-white/50'
                  }`}
                  aria-label={`Go to image ${idx + 1}`}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Value Proposition */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-blue-50/50">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-5xl sm:text-6xl font-bold text-foreground mb-6 text-balance">
            Smart Building Management System
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8 text-balance">
            AI-powered infrastructure complaint management for college campuses. Report issues, track resolutions, and maintain campus excellence.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link href="/login">
              <Button className="bg-primary hover:bg-blue-700 text-white px-8 py-6 text-lg gap-2 shadow-lg">
                Login to Dashboard
                <ArrowRight className="w-5 h-5" />
              </Button>
            </Link>
            <Link href="/register">
              <Button variant="outline" className="border-primary text-primary hover:bg-blue-50 px-8 py-6 text-lg">
                Report an Issue
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {[
              { number: '5000+', label: 'Active Users' },
              { number: '98%', label: 'Issue Resolution' },
              { number: '2.5h', label: 'Avg Response Time' },
              { number: '24/7', label: 'System Uptime' },
            ].map((stat, idx) => (
              <Card key={idx} className="bg-white border-blue-100 p-6 text-center hover:border-primary transition-colors">
                <div className="text-4xl font-bold text-primary mb-2">{stat.number}</div>
                <p className="text-muted-foreground font-medium">{stat.label}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* System Overview */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-foreground mb-4">How It Works</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Streamlined process from complaint to resolution
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card className="bg-blue-50/50 border-blue-100 p-8 hover:border-primary transition-colors">
              <div className="w-14 h-14 bg-primary text-white rounded-lg flex items-center justify-center mb-6 text-2xl font-bold">1</div>
              <h3 className="text-xl font-bold text-foreground mb-3">Report Issues</h3>
              <p className="text-muted-foreground">
                Students submit complaints with photos, location, and detailed descriptions using an intuitive form
              </p>
            </Card>
            <Card className="bg-blue-50/50 border-blue-100 p-8 hover:border-primary transition-colors">
              <div className="w-14 h-14 bg-primary text-white rounded-lg flex items-center justify-center mb-6 text-2xl font-bold">2</div>
              <h3 className="text-xl font-bold text-foreground mb-3">AI Classification</h3>
              <p className="text-muted-foreground">
                Intelligent system automatically categorizes and prioritizes complaints for optimal resource allocation
              </p>
            </Card>
            <Card className="bg-blue-50/50 border-blue-100 p-8 hover:border-primary transition-colors">
              <div className="w-14 h-14 bg-primary text-white rounded-lg flex items-center justify-center mb-6 text-2xl font-bold">3</div>
              <h3 className="text-xl font-bold text-foreground mb-3">Track & Resolve</h3>
              <p className="text-muted-foreground">
                Real-time monitoring of issue status with worker updates and automatic notifications
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-blue-50/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-foreground mb-4">Powerful Features</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Everything needed for modern campus management
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            <div className="space-y-6">
              <div className="flex gap-4">
                <CheckCircle className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
                <div>
                  <h3 className="text-lg font-bold text-foreground mb-2">AI Complaint Classification</h3>
                  <p className="text-muted-foreground">
                    Machine learning automatically categorizes issues by type, location, and severity for smart routing
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <CheckCircle className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
                <div>
                  <h3 className="text-lg font-bold text-foreground mb-2">Campus Building Database</h3>
                  <p className="text-muted-foreground">
                    Comprehensive inventory of all campus buildings, rooms, and facilities with maintenance history
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <CheckCircle className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
                <div>
                  <h3 className="text-lg font-bold text-foreground mb-2">SLA Monitoring</h3>
                  <p className="text-muted-foreground">
                    Track service level agreements with automated alerts and escalation procedures
                  </p>
                </div>
              </div>
            </div>
            <div className="space-y-6">
              <div className="flex gap-4">
                <CheckCircle className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
                <div>
                  <h3 className="text-lg font-bold text-foreground mb-2">Role-Based Dashboards</h3>
                  <p className="text-muted-foreground">
                    Customized interfaces for students, maintenance workers, and administrators with relevant metrics
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <CheckCircle className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
                <div>
                  <h3 className="text-lg font-bold text-foreground mb-2">Advanced Analytics</h3>
                  <p className="text-muted-foreground">
                    Detailed reports on maintenance trends, bottlenecks, and predictive maintenance insights
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <CheckCircle className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
                <div>
                  <h3 className="text-lg font-bold text-foreground mb-2">Real-time Notifications</h3>
                  <p className="text-muted-foreground">
                    Instant updates via email and in-app alerts for complaint status changes and urgent issues
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-foreground mb-4">What Users Say</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Real feedback from our campus community
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                name: 'Priya Sharma',
                role: 'Student',
                feedback: 'The app made reporting infrastructure issues so easy. I got a response within 2 hours!',
                rating: 5,
              },
              {
                name: 'Rajesh Kumar',
                role: 'Maintenance Worker',
                feedback: 'The AI classification helps us prioritize issues effectively. Our team is much more efficient now.',
                rating: 5,
              },
              {
                name: 'Dr. Anjali Desai',
                role: 'Campus Administrator',
                feedback: 'Excellent system! The analytics and reporting features give us valuable insights into campus infrastructure.',
                rating: 5,
              },
            ].map((testimonial, idx) => (
              <Card key={idx} className="bg-blue-50/50 border-blue-100 p-8">
                <div className="flex gap-1 mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 text-yellow-400 fill-yellow-400" />
                  ))}
                </div>
                <p className="text-muted-foreground mb-6 italic">
                  &ldquo;{testimonial.feedback}&rdquo;
                </p>
                <div className="border-t border-blue-100 pt-4">
                  <p className="font-bold text-foreground">{testimonial.name}</p>
                  <p className="text-sm text-muted-foreground">{testimonial.role}</p>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-primary text-white">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <h2 className="text-4xl font-bold mb-4">Ready to Transform Your Campus?</h2>
          <p className="text-lg text-blue-100 max-w-2xl mx-auto">
            Join thousands of users improving campus infrastructure management with SBMS
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link href="/login">
              <Button className="bg-white text-primary hover:bg-blue-50 px-8 py-6 text-lg font-semibold shadow-lg">
                Login to Dashboard
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link href="/register">
              <Button className="bg-blue-700 hover:bg-blue-800 text-white px-8 py-6 text-lg border border-white/30">
                Create New Account
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Building2 className="w-6 h-6 text-primary" />
              <span className="font-bold text-lg">SBMS</span>
            </div>
            <p className="text-gray-400 text-sm">Smart Building Management System for modern campuses. Powered by AI.</p>
          </div>
          <div>
            <h4 className="font-semibold mb-4 text-white">Product</h4>
            <ul className="space-y-2 text-gray-400 text-sm">
              <li><a href="#" className="hover:text-white transition-colors">Features</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Pricing</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Security</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-4 text-white">Company</h4>
            <ul className="space-y-2 text-gray-400 text-sm">
              <li><a href="#" className="hover:text-white transition-colors">About</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-4 text-white">Support</h4>
            <ul className="space-y-2 text-gray-400 text-sm">
              <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Help Center</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Status</a></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-700 pt-8">
          <p className="text-center text-gray-400 text-sm">
            © 2026 Smart Building Management System. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
