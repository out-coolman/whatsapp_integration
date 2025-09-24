import { motion } from "framer-motion";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Search,
  Filter,
  Plus,
  Eye,
  Edit,
  Phone,
  MessageCircle,
  MoreHorizontal
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { leadsService, Lead } from "@/services/leads";

const getStatusColor = (classification: string) => {
  switch (classification) {
    case "hot":
      return "bg-red-100 text-red-800";
    case "warm":
      return "bg-yellow-100 text-yellow-800";
    case "cold":
      return "bg-blue-100 text-blue-800";
    default:
      return "bg-muted text-muted-foreground";
  }
};

const getStageColor = (stage: string) => {
  switch (stage) {
    case "new":
      return "bg-muted text-muted-foreground";
    case "contacted":
      return "bg-blue-100 text-blue-800";
    case "qualified":
      return "bg-primary-soft text-primary";
    case "proposed":
      return "bg-accent-soft text-accent";
    case "booked":
      return "bg-success-soft text-success";
    case "confirmed":
      return "bg-green-100 text-green-800";
    default:
      return "bg-muted text-muted-foreground";
  }
};

export default function Leads() {
  const [searchTerm, setSearchTerm] = useState("");
  const [classificationFilter, setClassificationFilter] = useState("all");
  const [stageFilter, setStageFilter] = useState("all");

  // Fetch leads data with filters
  const { data: leadsData, isLoading: leadsLoading } = useQuery({
    queryKey: ['leads', searchTerm, classificationFilter, stageFilter],
    queryFn: () => leadsService.getLeadsWithFilters({
      search: searchTerm || undefined,
      classification: classificationFilter !== "all" ? classificationFilter : undefined,
      stage: stageFilter !== "all" ? stageFilter : undefined,
      limit: 100
    }),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const leads = leadsData || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-between items-center"
      >
        <div>
          <h1 className="text-3xl font-bold text-foreground">Leads & CRM</h1>
          <p className="text-muted-foreground">
            Manage your leads and track conversion progress
          </p>
        </div>
        <Button className="rounded-2xl bg-primary hover:bg-primary-hover">
          <Plus className="h-4 w-4 mr-2" />
          New Lead
        </Button>
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="rounded-2xl shadow-card border-border">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search leads by name or city..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 rounded-2xl border-border focus:ring-primary focus:border-primary"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Select value={classificationFilter} onValueChange={setClassificationFilter}>
                  <SelectTrigger className="w-32 rounded-2xl border-border">
                    <SelectValue placeholder="Classification" />
                  </SelectTrigger>
                  <SelectContent className="rounded-2xl">
                    <SelectItem value="all">All Classifications</SelectItem>
                    <SelectItem value="hot">Hot</SelectItem>
                    <SelectItem value="warm">Warm</SelectItem>
                    <SelectItem value="cold">Cold</SelectItem>
                  </SelectContent>
                </Select>
                
                <Select value={stageFilter} onValueChange={setStageFilter}>
                  <SelectTrigger className="w-32 rounded-2xl border-border">
                    <SelectValue placeholder="Stage" />
                  </SelectTrigger>
                  <SelectContent className="rounded-2xl">
                    <SelectItem value="all">All Stages</SelectItem>
                    <SelectItem value="new">New</SelectItem>
                    <SelectItem value="contacted">Contacted</SelectItem>
                    <SelectItem value="qualified">Qualified</SelectItem>
                    <SelectItem value="proposed">Proposed</SelectItem>
                    <SelectItem value="booked">Booked</SelectItem>
                    <SelectItem value="confirmed">Confirmed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Leads Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="rounded-2xl shadow-card border-border">
          <CardHeader>
            <CardTitle>Leads ({leads.length}) {leadsLoading && "(Loading...)"}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Phone</TableHead>
                    <TableHead>Stage</TableHead>
                    <TableHead>Classification</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Last Contact</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {leads.map((lead, index) => (
                    <motion.tr
                      key={lead.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3 + index * 0.05 }}
                      className="hover:bg-muted/50 transition-colors"
                    >
                      <TableCell className="font-medium">{lead.full_name}</TableCell>
                      <TableCell>{lead.email || "N/A"}</TableCell>
                      <TableCell className="font-mono text-sm">{lead.phone || "N/A"}</TableCell>
                      <TableCell>
                        <Badge className={`rounded-full ${getStageColor(lead.stage)}`}>
                          {lead.stage.charAt(0).toUpperCase() + lead.stage.slice(1)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={`rounded-full ${getStatusColor(lead.classification)}`}>
                          {lead.classification.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm capitalize">{lead.source.replace('_', ' ')}</span>
                      </TableCell>
                      <TableCell>
                        {lead.last_contacted_at
                          ? new Date(lead.last_contacted_at).toLocaleDateString()
                          : "Never"
                        }
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-lg hover:bg-secondary">
                            <Eye className="h-4 w-4" />
                          </Button>
                          {lead.phone && (
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-lg hover:bg-secondary">
                              <Phone className="h-4 w-4" />
                            </Button>
                          )}
                          {lead.phone && (
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-lg hover:bg-secondary">
                              <MessageCircle className="h-4 w-4" />
                            </Button>
                          )}
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-lg hover:bg-secondary">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent className="rounded-2xl" align="end">
                              <DropdownMenuItem className="rounded-xl">
                                <Edit className="h-4 w-4 mr-2" />
                                Edit Lead
                              </DropdownMenuItem>
                              <DropdownMenuItem className="rounded-xl">
                                View Details
                              </DropdownMenuItem>
                              <DropdownMenuItem className="rounded-xl">
                                Change Classification
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </TableCell>
                    </motion.tr>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}