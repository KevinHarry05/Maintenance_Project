'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Building2, Plus, Trash2, Search } from 'lucide-react';
import { useState } from 'react';
import { useBuildings, useCreateBuilding, useDeleteBuilding } from '@/hooks/useBuildings';

export default function BuildingsPage() {
  const { data: buildings = [], isLoading } = useBuildings();
  const createBuilding = useCreateBuilding();
  const deleteBuilding = useDeleteBuilding();

  const [searchTerm, setSearchTerm] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [newName, setNewName] = useState('');
  const [newBlock, setNewBlock] = useState('');
  const [newFloors, setNewFloors] = useState('');

  const filtered = buildings.filter((b) =>
    b.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    b.block.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await createBuilding.mutateAsync({ name: newName, block: newBlock, floor_count: Number(newFloors) });
    setNewName('');
    setNewBlock('');
    setNewFloors('');
    setShowForm(false);
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Buildings Management</h1>
          <p className="text-muted-foreground">Manage campus buildings and facilities</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)} className="bg-primary hover:bg-primary-dark text-primary-foreground gap-2">
          <Plus className="w-5 h-5" />
          Add Building
        </Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search buildings..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10 bg-input border-border text-foreground placeholder:text-muted-foreground h-11"
        />
      </div>

      {showForm && (
        <Card className="bg-card border-border p-6">
          <h2 className="text-lg font-semibold text-foreground mb-4">Add New Building</h2>
          <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Building Name</label>
              <Input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="e.g., Block E" className="bg-input border-border text-foreground" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Block</label>
              <Input value={newBlock} onChange={(e) => setNewBlock(e.target.value)} placeholder="e.g., E" className="bg-input border-border text-foreground" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Number of Floors</label>
              <Input type="number" value={newFloors} onChange={(e) => setNewFloors(e.target.value)} placeholder="5" className="bg-input border-border text-foreground" required />
            </div>
            <div className="flex items-end gap-2">
              <Button type="submit" disabled={createBuilding.isPending} className="bg-primary hover:bg-primary-dark text-primary-foreground">
                {createBuilding.isPending ? 'Saving…' : 'Save Building'}
              </Button>
              <Button type="button" variant="outline" className="border-border hover:bg-card text-foreground" onClick={() => setShowForm(false)}>
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      )}

      {isLoading ? (
        <p className="text-muted-foreground">Loading buildings…</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((building) => (
            <Card key={building.id} className="bg-card border-border p-6 hover:border-primary/50 transition-colors">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary/20 rounded-lg flex items-center justify-center">
                    <Building2 className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground">{building.name}</h3>
                    <p className="text-xs text-muted-foreground">Block {building.block}</p>
                  </div>
                </div>
              </div>

              <div className="space-y-3 mb-4 pb-4 border-b border-border">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Floors</span>
                  <span className="font-semibold text-foreground">{building.floor_count}</span>
                </div>
              </div>

              <Button
                size="sm"
                variant="outline"
                className="border-border hover:bg-red-500/10 text-red-400 gap-1 w-full"
                disabled={deleteBuilding.isPending}
                onClick={() => deleteBuilding.mutate(building.id)}
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </Button>
            </Card>
          ))}
          {filtered.length === 0 && (
            <p className="text-muted-foreground col-span-3">No buildings found.</p>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-card/50 border-border p-6">
          <p className="text-muted-foreground text-sm mb-2">Total Buildings</p>
          <p className="text-3xl font-bold text-foreground">{buildings.length}</p>
        </Card>
        <Card className="bg-card/50 border-border p-6">
          <p className="text-muted-foreground text-sm mb-2">Total Floors</p>
          <p className="text-3xl font-bold text-foreground">{buildings.reduce((s, b) => s + b.floor_count, 0)}</p>
        </Card>
      </div>
    </div>
  );
}

